from django.shortcuts import render, get_object_or_404, redirect
from pacientes.models import Paciente
from .models import Consulta, Receta, OrdenExamen
from .forms import ConsultaForm
from django.utils.timezone import now
from pagos.models import OrdenPago
from doctores.models import Doctor
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages

# ==============================================
# VISTAS PARA LABORATORIO
# ==============================================

def es_laboratorio(user):
    """Verifica si el usuario pertenece al grupo laboratorio"""
    return user.groups.filter(name='laboratorio').exists()

######################################
@login_required
@user_passes_test(es_laboratorio)
def lista_ordenes_pendientes(request):
    """
    Vista para que el laboratorio vea todas las órdenes
    (SOLO Laboratorio)
    """
    # Filtrar por estado y tipo de examen
    ordenes_pendientes = OrdenExamen.objects.filter(
        estado='SOLICITADO',
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente'
    ).order_by('-urgente', 'fecha_solicitud')

    ordenes_en_proceso = OrdenExamen.objects.filter(
        estado='EN_PROCESO',
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente'
    ).order_by('fecha_solicitud')

    # NUEVO: Órdenes COMPLETADAS
    ordenes_completados = OrdenExamen.objects.filter(
        estado='COMPLETADO',
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente'
    ).order_by('-fecha_realizacion')

    # NUEVO: Órdenes ENTREGADAS
    ordenes_entregados = OrdenExamen.objects.filter(
        estado='ENTREGADO',
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente'
    ).order_by('-fecha_realizacion')

    context = {
        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_en_proceso': ordenes_en_proceso,
        'ordenes_completados': ordenes_completados,  # NUEVO
        'ordenes_entregados': ordenes_entregados,    # NUEVO
        'es_laboratorio': True,
    }

    return render(request, 'consultas/laboratorio/lista_ordenes.html', context)

#########
@login_required
@user_passes_test(es_laboratorio)
def mis_ordenes_en_proceso(request):
    """
    Muestra solo las órdenes asignadas AL USUARIO ACTUAL
    (SOLO Laboratorio - SIN Ecografías)
    """
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',  # ← CAMBIADO: solo 'LABORATORIO'
        estado='EN_PROCESO',
        tecnico_asignado=request.user
    ).select_related(
        'consulta__paciente',
        'consulta__doctor__usuario'
    ).order_by('fecha_solicitud')

    context = {
        'ordenes': ordenes,
        'es_laboratorio': True,
    }

    return render(request, 'consultas/laboratorio/mis_ordenes.html', context)

####################################
@login_required
@user_passes_test(es_laboratorio)
def asignar_orden(request, orden_id):
    """Asignar una orden específica al laboratorista actual"""
    orden = get_object_or_404(OrdenExamen, id=orden_id)

    # VALIDACIONES
    # 1. ¿Es orden de laboratorio?
    if orden.tipo_examen != 'LABORATORIO':  # ← CAMBIADO: solo 'LABORATORIO'
        messages.error(request, '❌ Solo se pueden asignar órdenes de Laboratorio.')
        return redirect('lista_ordenes_pendientes')

    # 2. ¿Está en estado SOLICITADO?
    if orden.estado != 'SOLICITADO':
        estado_actual = orden.get_estado_display()
        messages.error(request, f'❌ La orden ya está {estado_actual.lower()}.')
        return redirect('lista_ordenes_pendientes')

    # 3. ¿Ya está asignada a alguien?
    if orden.tecnico_asignado:
        tecnico = orden.tecnico_asignado.get_full_name() or orden.tecnico_asignado.username
        messages.warning(request, f'⚠️ Ya está asignada a: {tecnico}')
        return redirect('lista_ordenes_pendientes')

    # ASIGNAR AL LABORATORISTA ACTUAL
    orden.estado = 'EN_PROCESO'
    orden.tecnico_asignado = request.user
    orden.fecha_asignacion = timezone.now()
    orden.save()

    # Mensaje personalizado
    user_name = request.user.get_full_name() or request.user.username
    messages.success(request, f'✅ Orden #{orden.id} asignada a: {user_name}')

    # Redirigir a "Mis Órdenes"
    return redirect('mis_ordenes_en_proceso')

################################
@login_required
@user_passes_test(es_laboratorio)
def detalle_orden_examen(request, orden_id):
    """
    Vista para ver detalles de una orden de examen
    (SOLO Laboratorio - SIN Ecografías)
    """
    orden = get_object_or_404(
        OrdenExamen.objects.select_related(
            'consulta__paciente',
            'consulta__doctor'
        ),
        id=orden_id,
        tipo_examen='LABORATORIO'
    )

    if request.method == 'POST':
        # Procesar formulario de atención
        accion = request.POST.get('accion')

        if accion == 'completar':
            # Solo marcar como COMPLETADO (sin registrar resultado)
            orden.estado = 'COMPLETADO'
            orden.fecha_realizacion = timezone.now()
            orden.save()
            messages.success(request, f'✅ Orden #{orden.id} marcada como completada')

        elif accion == 'entregar':
            # Marcar como ENTREGADO
            orden.estado = 'ENTREGADO'
            orden.fecha_entrega = timezone.now()  # NUEVO
            orden.save()
            messages.success(request, f'✅ Orden #{orden.id} marcada como entregada')

        return redirect('detalle_orden_examen', orden_id=orden.id)

    context = {
        'orden': orden,
        'paciente': orden.consulta.paciente,
        'consulta': orden.consulta,
        'es_laboratorio': True,
    }

    return render(request, 'consultas/laboratorio/detalle_orden.html', context)

################################
# ==============================================
# VISTAS PARA CONSULTAS
# ==============================================

def paciente_tiene_consulta_hoy(paciente, tarifa, doctor=None):
    """
    Verifica si un paciente ya tiene una consulta registrada hoy
    para el mismo tipo de consulta y especialidad.

    Reglas:
    - Un paciente NO puede tener 2 consultas del mismo tipo el mismo día
    - Ejemplo: No puede tener 2 GENERAL el mismo día
    - Pero SÍ puede tener GENERAL y OBSTETRICIA el mismo día
    """
    hoy = now().date()

    # Obtener todas las consultas del paciente hoy
    consultas_hoy = Consulta.objects.filter(
        paciente=paciente,
        fecha__date=hoy,
        estado=Consulta.EstadoConsulta.REGISTRADA
    )

    # Si no hay consultas hoy, está OK
    if not consultas_hoy.exists():
        return False

    # Verificar cada consulta existente
    for consulta_existente in consultas_hoy:
        # Caso 1: Ambas son GENERAL
        if (tarifa.tipo_consulta == 'GENERAL' and
            consulta_existente.tarifa.tipo_consulta == 'GENERAL'):
            return True  # Ya tiene GENERAL hoy

        # Caso 2: Ambas son ECOGRAFIA
        if (tarifa.tipo_consulta == 'ECOGRAFIA' and
            consulta_existente.tarifa.tipo_consulta == 'ECOGRAFIA'):
            return True  # Ya tiene ECOGRAFIA hoy

        # Caso 3: Ambas son ESPECIALIDAD y tienen la misma especialidad
        if (tarifa.tipo_consulta == 'ESPECIALIDAD' and
            consulta_existente.tarifa.tipo_consulta == 'ESPECIALIDAD' and
            tarifa.especialidad == consulta_existente.tarifa.especialidad):
            return True  # Ya tiene esta especialidad hoy

        # Caso 4: Validación por doctor si se especificó
        if doctor and consulta_existente.doctor == doctor:
            return True  # Ya tiene consulta con este doctor hoy

    return False  # No hay conflictos

def crear_consulta(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            tarifa = form.cleaned_data['tarifa']
            doctor = form.cleaned_data.get('doctor')
            hoy = now().date()

            # Validar si el paciente ya tiene consulta hoy del mismo tipo/especialidad
            existe = paciente_tiene_consulta_hoy(paciente, tarifa, doctor)
            if existe:
                # Determinar mensaje de error específico
                if tarifa.tipo_consulta == 'GENERAL':
                    mensaje_error = (
                        'El paciente ya tiene una consulta GENERAL '
                        'registrada para hoy.'
                    )
                elif tarifa.tipo_consulta == 'ECOGRAFIA':
                    mensaje_error = (
                        'El paciente ya tiene una ECOGRAFÍA '
                        'registrada para hoy.'
                    )
                elif tarifa.tipo_consulta == 'ESPECIALIDAD':
                    mensaje_error = (
                        f'El paciente ya tiene una consulta de {tarifa.get_especialidad_display()} '
                        'registrada para hoy.'
                    )
                else:
                    mensaje_error = (
                        'El paciente ya tiene una consulta '
                        'registrada para hoy.'
                    )

                return render(request, 'consultas/crear_consulta.html', {
                    'paciente': paciente,
                    'form': form,
                    'error': mensaje_error
                })
            
            # Si se seleccionó un doctor, validar también por doctor
            if doctor:
                existe_con_doctor = Consulta.objects.filter(
                    paciente=paciente,
                    doctor=doctor,
                    fecha__date=hoy,
                    estado=Consulta.EstadoConsulta.REGISTRADA
                ).exists()

                if existe_con_doctor:
                    return render(request, 'consultas/crear_consulta.html', {
                        'paciente': paciente,
                        'form': form,
                        'error': (
                            f'El paciente ya tiene una consulta registrada hoy '
                            f'con el Dr. {doctor.nombres} {doctor.apellidos}.'
                        )
                    })
            
            consulta = form.save(commit=False)
            consulta.paciente = paciente
            consulta.save()
            
            # Crear orden de pago asociada a la consulta
            orden = OrdenPago.objects.create(
                consulta=consulta
            )

            # Redirigir a la orden de pago
            return redirect('detalle_orden_pago', orden.id)

    else:
        form = ConsultaForm()

    return render(request, 'consultas/crear_consulta.html', {
        'paciente': paciente,
        'form': form
    })

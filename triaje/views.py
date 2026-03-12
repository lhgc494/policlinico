from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .models import Triaje
from .forms import TriajeForm, EditarTriajeForm
from consultas.models import Consulta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from config.decorators import grupo_requerido
from datetime import datetime
from notificaciones.models import Notificacion
###crear triaje########
@grupo_requerido('recepcion', 'administrador')
@login_required
def crear_triaje(request, consulta_id):
    """
    Crear o completar un triaje para una consulta.
    - Marca la consulta como EN_TRIAGE al iniciar
    - Al completar todos los campos, notifica al doctor
    """
    from notificaciones.models import Notificacion
    
    consulta = get_object_or_404(
        Consulta,
        pk=consulta_id,
        estado__in=[
            Consulta.EstadoConsulta.PAGADA,
            Consulta.EstadoConsulta.EN_TRIAGE
        ]
    )

    # Obtener o crear triaje asociado
    triaje, creado = Triaje.objects.get_or_create(
        consulta=consulta,
        defaults={
            'peso': None,
            'talla': None,
            'temperatura': None,
            'presion': '',
            'frecuencia_cardiaca': None,
            'saturacion': None
        }
    )

    if request.method == 'POST':
        form = TriajeForm(request.POST, instance=triaje)
        if form.is_valid():
            # Guardar el formulario - el modelo se encarga de cambiar estados
            form.save()
            
            # ✅ NOTIFICAR AL DOCTOR (si tiene usuario asignado)
            if consulta.doctor and consulta.doctor.usuario:
                Notificacion.objects.create(
                    usuario=consulta.doctor.usuario,
                    tipo_usuario='DOCTOR',
                    tipo='NUEVA_CONSULTA',
                    titulo='🔔 Nueva consulta pendiente',
                    mensaje=f'Paciente: {consulta.paciente.nombres} {consulta.paciente.apellidos}',
                    elemento_id=consulta.id
                )
                print(f"📨 Notificación enviada al Dr. {consulta.doctor.nombres}")

            messages.success(request, '✅ Triaje registrado correctamente. Paciente enviado a consulta.')
            return redirect('lista_triaje_pendiente')
        else:
            # SOLO DEBUG EN CONSOLA
            print("🔍 Errores del formulario:", form.errors)
            # NO ENVIAR MENSAJES DE ERROR - se muestran en template
            pass
    else:
        form = TriajeForm(instance=triaje)

    return render(request, 'triaje/triaje_form.html', {
        'form': form,
        'consulta': consulta
    })


##########################
@grupo_requerido('recepcion', 'administrador')
@login_required
def lista_triaje_pendiente(request):
    """
    Lista de consultas que necesitan triaje:
    - Consultas PAGADAS sin triaje creado
    - Consultas EN_TRIAGE con triaje INICIADO (no completado)
    - Excluye consultas con triaje COMPLETO
    """
    consultas = Consulta.objects.filter(
        estado__in=[
            Consulta.EstadoConsulta.PAGADA,
            Consulta.EstadoConsulta.EN_TRIAGE
        ]
    ).exclude(
        triaje__estado=Triaje.EstadoTriaje.COMPLETO
    ).select_related('paciente', 'triaje').order_by('fecha')

    paginator = Paginator(consultas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'triaje/lista_triaje_pendiente.html',
        {
            'page_obj': page_obj,
            'total_pendientes': consultas.count()
        }
    )

# Cambiar el permiso personalizado por el permiso estándar
@grupo_requerido('recepcion', 'administrador')
@login_required
@permission_required('triaje.view_triaje', raise_exception=True)
def historial_triajes(request):
    """
    Historial de triajes COMPLETADOS
    - Solo lectura para recepcionistas y administradores
    """
    triajes = Triaje.objects.filter(
        estado=Triaje.EstadoTriaje.COMPLETO
    ).select_related('consulta__paciente').order_by('-fecha')

    paginator = Paginator(triajes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'triaje/historial_triajes.html',
        {
            'page_obj': page_obj
        }
    )



#### editar triaje ########
@grupo_requerido('recepcion', 'administrador')
@login_required
@permission_required('triaje.change_triaje', raise_exception=True)
def editar_triaje(request, triaje_id):
    """
    Editar un triaje existente (solo para administradores)
    Permite corregir datos de triajes ya completados
    """
    triaje = get_object_or_404(Triaje, id=triaje_id)

    # Verificar que el triaje esté COMPLETO (solo se editan completados)
    if triaje.estado != Triaje.EstadoTriaje.COMPLETO:
        messages.warning(request, '⚠️ Solo se pueden editar triajes completados.')
        return redirect('historial_triajes')

    if request.method == 'POST':
        form = EditarTriajeForm(request.POST, instance=triaje)
        if form.is_valid():
            try:
                # Usar el método save() del formulario que usa update() directo
                form.save(triaje_id)
                messages.success(request, '✅ Triaje actualizado correctamente.')
                return redirect('historial_triajes')
            except Exception as e:
                print(f"Error al guardar: {e}")
                messages.error(request, f'❌ Error al guardar: {str(e)}')
        else:
            # SOLO DEBUG EN CONSOLA (opcional)
            print("=" * 50)
            print(f"🔍 ERRORES EN FORMULARIO - Triaje #{triaje_id}")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"  {field}: {error}")
            print("=" * 50)
            # NO ENVIAR MENSAJES DE ERROR - se muestran en template
            pass
    else:
        form = EditarTriajeForm(instance=triaje)

    return render(request, 'triaje/editar_triaje.html', {
        'form': form,
        'triaje': triaje
    })

#############
def saltar_triaje(request, consulta_id):
    from consultas.models import Consulta
    from .models import Triaje
    from pagos.models import OrdenPago
    from notificaciones.models import Notificacion
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from django.utils import timezone

    consulta = get_object_or_404(Consulta, pk=consulta_id)

    # ✅ TIPOS QUE PUEDEN SALTAR TRIAJE
    TIPOS_SIN_TRIAJE = ['LECTURA_RESULTADOS', 'ECOGRAFIA', 'TOPICO']

    if consulta.tipo_consulta not in TIPOS_SIN_TRIAJE:
        messages.error(request, '❌ Esta opción no está disponible para este tipo de consulta.')
        return redirect('crear_triaje', consulta_id=consulta.id)

    # Crear triaje con valores mínimos
    triaje, created = Triaje.objects.update_or_create(
        consulta=consulta,
        defaults={
            'peso': 1,
            'talla': 1,
            'temperatura': 36.5,
            'presion': "120/80",
            'frecuencia_cardiaca': 70,
            'saturacion': 98,
        }
    )
    triaje.save()

    # ========================================
    # COMPORTAMIENTO POR TIPO DE CONSULTA
    # ========================================

    # 📋 LECTURA DE RESULTADOS - Va al doctor
    if consulta.tipo_consulta == 'LECTURA_RESULTADOS':
        # ✅ NOTIFICAR AL DOCTOR
        if consulta.doctor and consulta.doctor.usuario:
            Notificacion.objects.create(
                usuario=consulta.doctor.usuario,
                tipo_usuario='DOCTOR',
                tipo='NUEVA_CONSULTA',
                titulo='🔔 Nueva lectura de resultados',
                mensaje=f'Paciente: {consulta.paciente.nombres} {consulta.paciente.apellidos}',
                elemento_id=consulta.id
            )
        messages.success(request, f'✅ Lectura de resultados enviada al Dr. {consulta.doctor.nombres} {consulta.doctor.apellidos}.')
        return redirect('lista_triaje_pendiente')

    # 📋 ECOGRAFÍA - Va al doctor
    if consulta.tipo_consulta == 'ECOGRAFIA':
        # ✅ NOTIFICAR AL DOCTOR
        if consulta.doctor and consulta.doctor.usuario:
            Notificacion.objects.create(
                usuario=consulta.doctor.usuario,
                tipo_usuario='DOCTOR',
                tipo='NUEVA_CONSULTA',
                titulo='🔔 Nueva ecografía pendiente',
                mensaje=f'Paciente: {consulta.paciente.nombres} {consulta.paciente.apellidos}',
                elemento_id=consulta.id
            )
        messages.success(request, f'✅ Ecografía enviada al Dr. {consulta.doctor.nombres} {consulta.doctor.apellidos}.')
        return redirect('lista_triaje_pendiente')

    # 📋 TÓPICO - NO va al doctor, va directo a pagos
    if consulta.tipo_consulta == 'TOPICO':
        # Asegurar que no tenga doctor
        if consulta.doctor:
            consulta.doctor = None
            consulta.save()

        # Buscar o crear orden de pago
        orden = OrdenPago.objects.filter(consulta=consulta).first()
        if not orden:
            orden = OrdenPago.objects.create(
                consulta=consulta,
                monto=consulta.precio,
                estado='PENDIENTE'
            )

        messages.success(request, f'✅ Tópico listo para cobro (S/{consulta.precio}).')
        return redirect('detalle_orden_pago', orden.id)

    # Fallback (no debería llegar aquí)
    return redirect('lista_triaje_pendiente')

#####

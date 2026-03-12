from consultas.models import CatalogoExamen, CatalogoEcografia
from django.http import JsonResponse
from farmacia.models import Medicamento
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from pacientes.models import Paciente
from triaje.models import Triaje
from consultas.forms import RecetaForm, OrdenExamenForm, EXAMENES_LABORATORIO, ECOGRAFIAS
from consultas.models import Consulta, Receta, OrdenExamen
from django.http import HttpResponseForbidden
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os
import json
from notificaciones.models import Notificacion
from django.contrib.auth.models import User
from config.decorators import grupo_requerido

####### buscar historial ########
@login_required
@grupo_requerido('doctores')
def buscar_historial(request):
    """
    Vista para buscar pacientes y ver su historial
    """
    query = request.GET.get('q', '')
    pacientes = None

    if query:
        pacientes = Paciente.objects.filter(
            Q(dni__icontains=query) |
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query)
        ).order_by('apellidos', 'nombres')[:10]

    return render(request, 'doctores/buscar_historial.html', {
        'pacientes': pacientes,
        'query': query
    })

######listado consultas##########
@login_required
@grupo_requerido('doctores')
def lista_consultas(request):
    """
    Vista para que el doctor vea sus consultas asignadas
    """
    try:
        doctor = request.user.doctor
        filtro_estado = request.GET.get('estado', 'pendientes')
        consultas = Consulta.objects.filter(doctor=doctor)

        if filtro_estado == 'pendientes':
            consultas = consultas.filter(estado='TRIAJE_COMPLETO')
        elif filtro_estado == 'atendidas':
            consultas = consultas.filter(estado='ATENDIDA')

        consultas = consultas.order_by('-fecha')

        return render(request, 'doctores/lista_consultas.html', {
            'consultas': consultas,
            'doctor': doctor,
            'filtro_actual': filtro_estado,
            'total_pendientes': Consulta.objects.filter(doctor=doctor, estado='TRIAJE_COMPLETO').count(),
            'total_atendidas': Consulta.objects.filter(doctor=doctor, estado='ATENDIDA').count(),
            'total_todas': Consulta.objects.filter(doctor=doctor).count(),
        })

    except AttributeError:
        return render(request, 'doctores/error.html', {
            'mensaje': 'No tiene un perfil de doctor asociado.'
        })

##########################################
@login_required
@grupo_requerido('doctores')
def atender_consulta(request, consulta_id):
    from notificaciones.models import Notificacion

    consulta = get_object_or_404(Consulta, id=consulta_id)

    # ✅ MARCAR NOTIFICACIONES COMO LEÍDAS
    if request.user.is_authenticated:
        Notificacion.objects.filter(
            usuario=request.user,
            elemento_id=consulta_id,
            tipo='NUEVA_CONSULTA'
        ).update(leida=True)
    consulta = get_object_or_404(Consulta, id=consulta_id)
    paciente = consulta.paciente
    triaje = Triaje.objects.filter(consulta=consulta).first()

    # 📌 IMPORTS PARA NOTIFICACIONES
    from notificaciones.models import Notificacion
    from django.contrib.auth.models import User
    from django.contrib import messages

    # Obtener exámenes de laboratorio ACTIVOS del catálogo
    examenes_laboratorio = CatalogoExamen.objects.filter(
        tipo='LABORATORIO',
        activo=True
    ).order_by('nombre')

    # Obtener ecografías ACTIVAS del catálogo específico
    ecografias = CatalogoEcografia.objects.filter(
        activo=True
    ).order_by('nombre')

    # Convertir a lista de tuplas para compatibilidad con el template
    examenes_laboratorio_list = [(examen.nombre, examen.nombre) for examen in examenes_laboratorio]
    ecografias_list = [(eco.nombre, eco.nombre) for eco in ecografias]

    # Agregar opción "OTRO" al final de cada lista
    examenes_laboratorio_list.append(('OTRO', 'OTRO (Especificar)'))
    ecografias_list.append(('OTRO', 'OTRO (Especificar)'))

    # Obtener medicamentos para el autocomplete
    medicamentos = Medicamento.objects.all()

    # Inicializar sesiones si no existen
    if 'recetas_temp' not in request.session:
        request.session['recetas_temp'] = []
    if 'laboratorio_temp' not in request.session:
        request.session['laboratorio_temp'] = []
    if 'ecografias_temp' not in request.session:
        request.session['ecografias_temp'] = []

    if request.method == 'POST':
        # ============================================
        # 1. AGREGAR RECETA TEMPORAL
        # ============================================
        if 'agregar_receta_temp' in request.POST:
            medicamento = request.POST.get('medicamento', '').strip()
            dosis = request.POST.get('dosis', '').strip()
            frecuencia = request.POST.get('frecuencia', '').strip()
            duracion = request.POST.get('duracion', '').strip()
            indicaciones = request.POST.get('indicaciones_receta', '').strip()

            if medicamento:
                recetas_existentes = [r['medicamento'] for r in request.session.get('recetas_temp', [])]
                if medicamento in recetas_existentes:
                    messages.warning(request, f"⚠️ El medicamento '{medicamento}' ya está en la lista")
                else:
                    nueva_receta = {
                        'medicamento': medicamento,
                        'dosis': dosis,
                        'frecuencia': frecuencia,
                        'duracion': duracion,
                        'indicaciones': indicaciones
                    }
                    request.session['recetas_temp'].append(nueva_receta)
                    request.session.modified = True
                    messages.success(request, f"✅ Medicamento '{medicamento}' agregado")
            return redirect('atender_consulta', consulta_id=consulta_id)

        # ============================================
        # 2. AGREGAR EXAMEN DE LABORATORIO TEMPORAL
        # ============================================
        elif 'agregar_lab_temp' in request.POST:
            examen = request.POST.get('examen_lab', '').strip()
            examen_otro = request.POST.get('examen_lab_otro', '').strip()
            indicaciones = request.POST.get('indicaciones_lab', '').strip()

            if examen:
                if examen == 'OTRO' and examen_otro:
                    examen_final = f"OTRO: {examen_otro}"
                else:
                    examen_final = examen

                examenes_existentes = [e['examen'] for e in request.session.get('laboratorio_temp', [])]
                if examen_final in examenes_existentes:
                    messages.warning(request, f"⚠️ El examen '{examen_final}' ya está en la lista")
                else:
                    nuevo_examen = {
                        'examen': examen_final,
                        'indicaciones': indicaciones
                    }
                    request.session['laboratorio_temp'].append(nuevo_examen)
                    request.session.modified = True
                    messages.success(request, f"✅ Examen de laboratorio '{examen_final}' agregado")
            return redirect('atender_consulta', consulta_id=consulta_id)

        # ============================================
        # 3. AGREGAR ECOGRAFÍA TEMPORAL
        # ============================================
        elif 'agregar_eco_temp' in request.POST:
            examen = request.POST.get('examen_eco', '').strip()
            examen_otro = request.POST.get('examen_eco_otro', '').strip()
            indicaciones = request.POST.get('indicaciones_eco', '').strip()

            if examen:
                if examen == 'OTRO' and examen_otro:
                    examen_final = f"OTRO: {examen_otro}"
                else:
                    examen_final = examen

                examenes_existentes = [e['examen'] for e in request.session.get('ecografias_temp', [])]
                if examen_final in examenes_existentes:
                    messages.warning(request, f"⚠️ La ecografía '{examen_final}' ya está en la lista")
                else:
                    nueva_ecografia = {
                        'examen': examen_final,
                        'indicaciones': indicaciones
                    }
                    request.session['ecografias_temp'].append(nueva_ecografia)
                    request.session.modified = True
                    messages.success(request, f"✅ Ecografía '{examen_final}' agregada")
            return redirect('atender_consulta', consulta_id=consulta_id)

        # ============================================
        # 4. ELIMINAR ITEMS TEMPORALES
        # ============================================
        elif 'eliminar_receta' in request.POST:
            index = int(request.POST.get('receta_index', -1))
            if 0 <= index < len(request.session['recetas_temp']):
                removed = request.session['recetas_temp'].pop(index)
                request.session.modified = True
                messages.info(request, f"❌ Medicamento '{removed['medicamento']}' eliminado")
            return redirect('atender_consulta', consulta_id=consulta_id)

        elif 'eliminar_laboratorio' in request.POST:
            index = int(request.POST.get('lab_index', -1))
            if 0 <= index < len(request.session['laboratorio_temp']):
                removed = request.session['laboratorio_temp'].pop(index)
                request.session.modified = True
                messages.info(request, f"❌ Examen '{removed['examen']}' eliminado")
            return redirect('atender_consulta', consulta_id=consulta_id)

        elif 'eliminar_ecografia' in request.POST:
            index = int(request.POST.get('eco_index', -1))
            if 0 <= index < len(request.session['ecografias_temp']):
                removed = request.session['ecografias_temp'].pop(index)
                request.session.modified = True
                messages.info(request, f"❌ Ecografía '{removed['examen']}' eliminado")
            return redirect('atender_consulta', consulta_id=consulta_id)

        # ============================================
        # 5. FINALIZAR CONSULTA (GUARDAR DEFINITIVO + NOTIFICACIONES)
        # ============================================
        elif 'guardar_definitivo' in request.POST:
            print(f"DEBUG - Guardando consulta {consulta_id}")

            # 🔴🔴🔴 CAMBIOS AQUÍ 🔴🔴🔴
            # OBTENER LOS NUEVOS CAMPOS DEL FORMULARIO
            motivo_consulta = request.POST.get('motivo_consulta', '').strip()
            diagnostico = request.POST.get('diagnostico', '').strip()
            examen_fisico = request.POST.get('examen_fisico', '').strip()  # ANTES era 'observaciones'
            tratamiento = request.POST.get('tratamiento', '').strip()

            print(f"DEBUG - Motivo consulta: '{motivo_consulta}'")
            print(f"DEBUG - Diagnóstico recibido: '{diagnostico}'")
            print(f"DEBUG - Examen físico: '{examen_fisico}'")
            print(f"DEBUG - Tratamiento recibido: '{tratamiento}'")

            # VALIDAR CAMPOS OBLIGATORIOS
            if not diagnostico:
                messages.error(request, "❌ El diagnóstico es obligatorio")
                return redirect('atender_consulta', consulta_id=consulta_id)

            if not tratamiento:
                messages.error(request, "❌ El tratamiento es obligatorio")
                return redirect('atender_consulta', consulta_id=consulta_id)

            # ACTUALIZAR LA CONSULTA CON LOS NUEVOS CAMPOS
            consulta.motivo_consulta = motivo_consulta
            consulta.diagnostico = diagnostico
            consulta.examen_fisico = examen_fisico  # ANTES era 'observaciones'
            consulta.tratamiento = tratamiento
            consulta.estado = 'ATENDIDA'
            consulta.save()

            print(f"DEBUG - Consulta actualizada. Diagnóstico guardado: '{consulta.diagnostico}'")

            # ============================================
            # 📋 CREAR RECETAS Y NOTIFICAR A FARMACIA
            # ============================================
            recetas_creadas = []
            recetas_temp = request.session.get('recetas_temp', [])

            for receta_data in recetas_temp:
                receta = Receta.objects.create(
                    consulta=consulta,
                    medicamento=receta_data['medicamento'],
                    dosis=receta_data.get('dosis', ''),
                    frecuencia=receta_data.get('frecuencia', ''),
                    duracion=receta_data.get('duracion', ''),
                    indicaciones=receta_data.get('indicaciones', '')
                )
                recetas_creadas.append(receta)

            # 🔔 NOTIFICAR A FARMACIA (si hay recetas)
            if recetas_creadas:
                usuarios_farmacia = User.objects.filter(groups__name='Farmacia')
                for usuario in usuarios_farmacia:
                    Notificacion.objects.create(
                        usuario=usuario,
                        tipo_usuario='FARMACIA',
                        tipo='NUEVA_RECETA',
                        titulo='🔔 Nuevas recetas pendientes',
                        mensaje=f'Paciente: {paciente.nombres} {paciente.apellidos} - {len(recetas_creadas)} receta(s)',
                        elemento_id=consulta.id
                    )
                print(f"📨 Notificaciones enviadas a {usuarios_farmacia.count()} usuarios de farmacia")

            # ============================================
            # 🧪 CREAR EXÁMENES DE LABORATORIO Y NOTIFICAR
            # ============================================
            examenes_creados = []
            laboratorio_temp = request.session.get('laboratorio_temp', [])

            for examen_data in laboratorio_temp:
                examen = examen_data['examen']
                if examen.startswith('OTRO:'):
                    tipo_examen = 'OTRO'
                    examen_especifico = examen[6:]
                else:
                    tipo_examen = 'LABORATORIO'
                    examen_especifico = examen

                orden = OrdenExamen.objects.create(
                    consulta=consulta,
                    tipo_examen=tipo_examen,
                    examen_especifico=examen_especifico,
                    indicaciones=examen_data.get('indicaciones', ''),
                    estado='SOLICITADO'
                )
                examenes_creados.append(orden)

            # 🔔 NOTIFICAR A LABORATORIO (si hay exámenes)
            if examenes_creados:
                usuarios_lab = User.objects.filter(groups__name='Laboratorio')
                for usuario in usuarios_lab:
                    Notificacion.objects.create(
                        usuario=usuario,
                        tipo_usuario='LABORATORIO',
                        tipo='NUEVO_EXAMEN',
                        titulo='🔔 Nuevos exámenes pendientes',
                        mensaje=f'Paciente: {paciente.nombres} {paciente.apellidos} - {len(examenes_creados)} examen(es)',
                        elemento_id=consulta.id
                    )
                print(f"📨 Notificaciones enviadas a {usuarios_lab.count()} usuarios de laboratorio")

            # ============================================
            # 📷 CREAR ECOGRAFÍAS (SIN NOTIFICACIÓN)
            # ============================================
            ecografias_creadas = []
            ecografias_temp = request.session.get('ecografias_temp', [])

            for examen_data in ecografias_temp:
                examen = examen_data['examen']
                if examen.startswith('OTRO:'):
                    tipo_examen = 'OTRO'
                    examen_especifico = examen[6:]
                else:
                    tipo_examen = 'ECOGRAFIA'
                    examen_especifico = examen

                orden = OrdenExamen.objects.create(
                    consulta=consulta,
                    tipo_examen=tipo_examen,
                    examen_especifico=examen_especifico,
                    indicaciones=examen_data.get('indicaciones', ''),
                    estado='SOLICITADO'
                )
                ecografias_creadas.append(orden)

            # ❌ NO NOTIFICAR PARA ECOGRAFÍAS
            if ecografias_creadas:
                print(f"📊 {len(ecografias_creadas)} ecografía(s) creadas (sin notificación)")

            # LIMPIAR SESIÓN TEMPORAL
            request.session['recetas_temp'] = []
            request.session['laboratorio_temp'] = []
            request.session['ecografias_temp'] = []
            request.session.modified = True

            messages.success(request, "✅ Consulta completada exitosamente")
            return redirect('doctor_consultas')

    # CONTEXTO PARA EL TEMPLATE
    context = {
        'consulta': consulta,
        'paciente': paciente,
        'triaje': triaje,
        'medicamentos': medicamentos,
        'examenes_laboratorio': examenes_laboratorio_list,
        'ecografias': ecografias_list,
        'examenes_laboratorio_objs': examenes_laboratorio,
        'ecografias_objs': ecografias,
        'recetas_temp': request.session.get('recetas_temp', []),
        'laboratorio_temp': request.session.get('laboratorio_temp', []),
        'ecografias_temp': request.session.get('ecografias_temp', []),
    }

    return render(request, 'doctores/atender_consulta.html', context)


########################
@login_required
@grupo_requerido('doctores')
def eliminar_item_temporal(request):
    """Eliminar un item temporal de la sesión"""
    if request.method == 'GET':
        tipo = request.GET.get('tipo')
        index = request.GET.get('index')

        if not tipo or not index:
            return JsonResponse({'success': False, 'error': 'Parámetros faltantes'})

        try:
            index = int(index)

            if tipo == 'receta':
                recetas_temp = request.session.get('recetas_temp', [])
                if 0 <= index < len(recetas_temp):
                    eliminado = recetas_temp.pop(index)
                    request.session['recetas_temp'] = recetas_temp
                    return JsonResponse({'success': True, 'mensaje': 'Receta eliminada'})

            elif tipo == 'laboratorio':
                ordenes_temp = request.session.get('laboratorio_temp', [])
                if 0 <= index < len(ordenes_temp):
                    eliminado = ordenes_temp.pop(index)
                    request.session['laboratorio_temp'] = ordenes_temp
                    return JsonResponse({'success': True, 'mensaje': 'Orden eliminada'})

            elif tipo == 'ecografia':
                ecografias_temp = request.session.get('ecografias_temp', [])
                if 0 <= index < len(ecografias_temp):
                    eliminado = ecografias_temp.pop(index)
                    request.session['ecografias_temp'] = ecografias_temp
                    return JsonResponse({'success': True, 'mensaje': 'Ecografía eliminada'})

            return JsonResponse({'success': False, 'error': 'Índice inválido'})

        except (ValueError, IndexError) as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@grupo_requerido('doctores')
def limpiar_temporales(request):
    """Limpiar todos los items temporales"""
    if request.method == 'POST':
        request.session['recetas_temp'] = []
        request.session['laboratorio_temp'] = []
        request.session['ecografias_temp'] = []

        messages.success(request, 'Todos los items temporales han sido eliminados')
        return redirect(request.META.get('HTTP_REFERER', 'doctor_consultas'))

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

##################
##### historial paciente####
# doctores/views.py - Modificar historial_paciente

@login_required
@grupo_requerido('doctores')
def historial_paciente(request, paciente_id):
    """
    Vista para ver el historial médico completo de un paciente
    """
    # Obtener el paciente
    paciente = get_object_or_404(Paciente, id=paciente_id)

    # Obtener todas las consultas de este paciente
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha')

    # Obtener todas las recetas de estas consultas
    recetas = Receta.objects.filter(consulta__in=consultas).order_by('-fecha_creacion')

    # Obtener todos los exámenes (laboratorio + ecografías)
    examenes = OrdenExamen.objects.filter(consulta__in=consultas).order_by('-fecha_solicitud')

    # Separar exámenes por tipo
    examenes_laboratorio = examenes.filter(tipo_examen='LABORATORIO')
    examenes_ecografias = examenes.filter(tipo_examen='ECOGRAFIA')
    examenes_otros = examenes.exclude(tipo_examen__in=['LABORATORIO', 'ECOGRAFIA'])

    # Obtener todos los triajes
    triajes = Triaje.objects.filter(consulta__in=consultas)

    return render(request, 'doctores/historial_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'recetas': recetas,
        'examenes_laboratorio': examenes_laboratorio,
        'examenes_ecografias': examenes_ecografias,
        'examenes_otros': examenes_otros,
        'triajes': triajes,
    })
#########
@login_required
@grupo_requerido('doctores')
def editar_receta(request, receta_id):
    """
    Vista para editar una receta existente
    """
    # Obtener la receta y verificar que pertenezca a una consulta del doctor
    receta = get_object_or_404(Receta, id=receta_id)

    # Verificar que el doctor es el dueño de esta consulta
    if receta.consulta.doctor != request.user.doctor:
        return HttpResponseForbidden("No tiene permiso para editar esta receta")

    if request.method == 'POST':
        form = RecetaForm(request.POST, instance=receta)
        if form.is_valid():
            form.save()
            return redirect('atender_consulta', consulta_id=receta.consulta.id)
    else:
        form = RecetaForm(instance=receta)

    return render(request, 'doctores/editar_receta.html', {
        'form': form,
        'receta': receta,
        'consulta': receta.consulta,
        'paciente': receta.consulta.paciente
    })

@login_required
@grupo_requerido('doctores')
def eliminar_receta(request, receta_id):
    """
    Vista para eliminar una receta
    """
    receta = get_object_or_404(Receta, id=receta_id)

    # Verificar que el doctor es el dueño
    if receta.consulta.doctor != request.user.doctor:
        return HttpResponseForbidden("No tiene permiso para eliminar esta receta")

    consulta_id = receta.consulta.id

    if request.method == 'POST':
        receta.delete()
        return redirect('atender_consulta', consulta_id=consulta_id)

    return render(request, 'doctores/eliminar_receta.html', {
        'receta': receta,
        'paciente': receta.consulta.paciente
    })

######### orden de examenes
@login_required
@grupo_requerido('doctores')
def editar_orden_examen(request, orden_id):
    """
    Vista para editar una orden de examen
    """
    orden = get_object_or_404(OrdenExamen, id=orden_id)

    if orden.consulta.doctor != request.user.doctor:
        return HttpResponseForbidden("No tiene permiso para editar esta orden")

    if request.method == 'POST':
        form = OrdenExamenForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            return redirect('atender_consulta', consulta_id=orden.consulta.id)
    else:
        form = OrdenExamenForm(instance=orden)

    return render(request, 'doctores.html', {
        'form': form,
        'orden': orden,
        'consulta': orden.consulta,
        'paciente': orden.consulta.paciente
    })
@login_required
@grupo_requerido('doctores')
def eliminar_orden_examen(request, orden_id):
    """
    Vista para eliminar una orden de examen
    """
    orden = get_object_or_404(OrdenExamen, id=orden_id)

    if orden.consulta.doctor != request.user.doctor:
        return HttpResponseForbidden("No tiene permiso para eliminar esta orden")

    consulta_id = orden.consulta.id

    if request.method == 'POST':
        orden.delete()
        return redirect('atender_consulta', consulta_id=consulta_id)

    return render(request, 'doctores/eliminar_orden_examen.html', {
        'orden': orden,
        'paciente': orden.consulta.paciente
    })


# AGREGAR ESTA FUNCIÓN (sugiero después de las importaciones, antes de buscar_historial)
@login_required
@grupo_requerido('doctores')
def buscar_medicamentos_ajax(request):
    """
    Búsqueda AJAX simple - solo nombres de medicamentos
    """
    # Verificar que sea doctor
    if not request.user.groups.filter(name='doctores').exists():
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)

    query = request.GET.get('q', '').strip().lower()

    if len(query) < 2:
        return JsonResponse({'medicamentos': []})

    try:
        # Buscar solo por nombre comercial (simplificado)
        medicamentos = Medicamento.objects.filter(
            activo=True,
            nombre_comercial__icontains=query
        ).order_by('nombre_comercial')[:10]

        # Solo devolver nombres
        resultados = []
        for med in medicamentos:
            resultados.append({
                'nombre': med.nombre_comercial,
                'nombre_completo': med.nombre_comercial
            })

        return JsonResponse({'medicamentos': resultados})

    except Exception as e:
        return JsonResponse({'medicamentos': []})


# doctores/views.py - AGREGAR SOLO ESTA FUNCIÓN (al final)

@login_required
@grupo_requerido('doctores')
def agregar_receta_temp_ajax(request):
    """
    Agregar receta temporal usando AJAX
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            # Inicializar sesión si no existe
            if 'recetas_temp' not in request.session:
                request.session['recetas_temp'] = []
            
            medicamento = data.get('medicamento', '').strip()
            dosis = data.get('dosis', '').strip()
            frecuencia = data.get('frecuencia', '').strip()
            duracion = data.get('duracion', '').strip()
            indicaciones = data.get('indicaciones', '').strip()
            
            if not medicamento:
                return JsonResponse({
                    'success': False,
                    'error': 'El medicamento es obligatorio'
                })
            
            # Validar duplicados
            recetas_existentes = [r['medicamento'] for r in request.session.get('recetas_temp', [])]
            if medicamento in recetas_existentes:
                return JsonResponse({
                    'success': False,
                    'error': f'El medicamento "{medicamento}" ya está en la lista'
                })
            
            # Agregar a sesión
            nueva_receta = {
                'medicamento': medicamento,
                'dosis': dosis,
                'frecuencia': frecuencia,
                'duracion': duracion,
                'indicaciones': indicaciones
            }
            
            request.session['recetas_temp'].append(nueva_receta)
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'Medicamento "{medicamento}" agregado',
                'total': len(request.session['recetas_temp']),
                'receta': nueva_receta
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

##############
# Mantén solo ESTAS funciones (elimina las otras duplicadas):

@login_required
@grupo_requerido('doctores')
def agregar_receta_temp_ajax(request):
    """Agregar receta temporal usando AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            if 'recetas_temp' not in request.session:
                request.session['recetas_temp'] = []
            
            medicamento = data.get('medicamento', '').strip()
            dosis = data.get('dosis', '').strip()
            frecuencia = data.get('frecuencia', '').strip()
            duracion = data.get('duracion', '').strip()
            indicaciones = data.get('indicaciones', '').strip()
            
            if not medicamento:
                return JsonResponse({
                    'success': False,
                    'error': 'El medicamento es obligatorio'
                })
            
            # Validar duplicados
            recetas_existentes = [r['medicamento'] for r in request.session.get('recetas_temp', [])]
            if medicamento in recetas_existentes:
                return JsonResponse({
                    'success': False,
                    'error': f'El medicamento "{medicamento}" ya está en la lista'
                })
            
            # Agregar a sesión
            nueva_receta = {
                'medicamento': medicamento,
                'dosis': dosis,
                'frecuencia': frecuencia,
                'duracion': duracion,
                'indicaciones': indicaciones
            }
            
            request.session['recetas_temp'].append(nueva_receta)
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'Medicamento "{medicamento}" agregado',
                'total': len(request.session['recetas_temp']),
                'receta': nueva_receta
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@grupo_requerido('doctores')
def agregar_lab_temp_ajax(request):
    """Agregar examen de laboratorio temporal usando AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            if 'laboratorio_temp' not in request.session:
                request.session['laboratorio_temp'] = []
            
            examen = data.get('examen', '').strip()
            examen_otro = data.get('examen_otro', '').strip()
            indicaciones = data.get('indicaciones', '').strip()
            
            if not examen:
                return JsonResponse({
                    'success': False,
                    'error': 'El examen es obligatorio'
                })
            
            # Manejar opción "OTRO"
            if examen == 'OTRO' and examen_otro:
                examen_final = f"OTRO: {examen_otro}"
            else:
                examen_final = examen
            
            # Validar duplicados
            examenes_existentes = [e['examen'] for e in request.session.get('laboratorio_temp', [])]
            if examen_final in examenes_existentes:
                return JsonResponse({
                    'success': False,
                    'error': f'El examen "{examen_final}" ya está en la lista'
                })
            
            # Agregar a sesión
            nuevo_examen = {
                'examen': examen_final,
                'indicaciones': indicaciones
            }
            
            request.session['laboratorio_temp'].append(nuevo_examen)
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'Examen "{examen_final}" agregado',
                'total': len(request.session['laboratorio_temp']),
                'examen': nuevo_examen
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@grupo_requerido('doctores')
def agregar_eco_temp_ajax(request):
    """Agregar ecografía temporal usando AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            if 'ecografias_temp' not in request.session:
                request.session['ecografias_temp'] = []
            
            examen = data.get('examen', '').strip()
            examen_otro = data.get('examen_otro', '').strip()
            indicaciones = data.get('indicaciones', '').strip()
            
            if not examen:
                return JsonResponse({
                    'success': False,
                    'error': 'La ecografía es obligatoria'
                })
            
            # Manejar opción "OTRO"
            if examen == 'OTRO' and examen_otro:
                examen_final = f"OTRO: {examen_otro}"
            else:
                examen_final = examen
            
            # Validar duplicados
            examenes_existentes = [e['examen'] for e in request.session.get('ecografias_temp', [])]
            if examen_final in examenes_existentes:
                return JsonResponse({
                    'success': False,
                    'error': f'La ecografía "{examen_final}" ya está en la lista'
                })
            
            # Agregar a sesión
            nueva_ecografia = {
                'examen': examen_final,
                'indicaciones': indicaciones
            }
            
            request.session['ecografias_temp'].append(nueva_ecografia)
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': f'Ecografía "{examen_final}" agregada',
                'total': len(request.session['ecografias_temp']),
                'ecografia': nueva_ecografia
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# doctores/views.py - AGREGAR AL FINAL (después de las funciones AJAX)
# doctores/views.py - MODIFICAR LAS 3 VISTAS

@login_required
@grupo_requerido('doctores')
def imprimir_recetas(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    paciente = consulta.paciente
    
    # Obtener recetas de la sesión temporal o de la BD
    if 'recetas_temp' in request.session and request.session['recetas_temp']:
        recetas = request.session['recetas_temp']
    else:
        recetas = Receta.objects.filter(consulta=consulta)
        recetas = [{
            'medicamento': r.medicamento,
            'dosis': r.dosis,
            'frecuencia': r.frecuencia,
            'duracion': r.duracion,
            'indicaciones': r.indicaciones
        } for r in recetas]
    
    # Determinar tipo de impresión
    tipo_impresion = request.GET.get('tipo', 'normal')
    
    context = {
        'consulta': consulta,
        'paciente': paciente,
        'recetas': recetas,
        'fecha_actual': timezone.now().date(),
        'tipo_impresion': tipo_impresion,
    }
    
    # Elegir template según tipo
    if tipo_impresion == 'termica':
        return render(request, 'doctores/imprimir/recetas_termica.html', context)
    else:
        return render(request, 'doctores/imprimir/recetas.html', context)


@login_required
@grupo_requerido('doctores','laboratorio')
def imprimir_laboratorio(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    paciente = consulta.paciente
    
    # Obtener exámenes de laboratorio
    if 'laboratorio_temp' in request.session and request.session['laboratorio_temp']:
        examenes = request.session['laboratorio_temp']
    else:
        examenes = OrdenExamen.objects.filter(
            consulta=consulta,
            tipo_examen='LABORATORIO'
        )
        examenes = [{
            'examen': e.examen_especifico,
            'indicaciones': e.indicaciones
        } for e in examenes]
    
    # Determinar tipo de impresión
    tipo_impresion = request.GET.get('tipo', 'normal')
    
    context = {
        'consulta': consulta,
        'paciente': paciente,
        'examenes': examenes,
        'fecha_actual': timezone.now().date(),
        'tipo_impresion': tipo_impresion,
    }
    
    if tipo_impresion == 'termica':
        return render(request, 'doctores/imprimir/laboratorio_termica.html', context)
    else:
        return render(request, 'doctores/imprimir/laboratorio.html', context)

#######
@login_required
@grupo_requerido('doctores')
def imprimir_ecografias(request, consulta_id):
    consulta = get_object_or_404(Consulta, id=consulta_id)
    paciente = consulta.paciente

    # Obtener ecografías
    if 'ecografias_temp' in request.session and request.session['ecografias_temp']:
        ecografias = request.session['ecografias_temp']
    else:
        ecografias = OrdenExamen.objects.filter(
            consulta=consulta,
            tipo_examen='ECOGRAFIA'
        )
        ecografias = [{
            'examen': e.examen_especifico,
            'indicaciones': e.indicaciones
        } for e in ecografias]

    # Determinar tipo de impresión
    tipo_impresion = request.GET.get('tipo', 'normal')

    context = {
        'consulta': consulta,  # CORREGIDO: estaba 'consulte'
        'paciente': paciente,
        'ecografias': ecografias,
        'fecha_actual': timezone.now().date(),
        'tipo_impresion': tipo_impresion,
    }

    if tipo_impresion == 'termica':
        return render(request, 'doctores/imprimir/ecografias_termica.html', context)
    else:
        return render(request, 'doctores/imprimir/ecografias.html', context)



# doctores/views.py - VERSIÓN CON WEASYPRINT (más simple)
@login_required
@grupo_requerido('doctores')
def exportar_historial_pdf(request, paciente_id):
    """Versión simple de exportación PDF"""
    try:
        paciente = get_object_or_404(Paciente, id=paciente_id)
        consultas = Consulta.objects.filter(paciente=paciente).order_by('-fecha')

        print(f"📊 Exportando PDF para paciente {paciente_id}")
        print(f"📋 Consultas encontradas: {consultas.count()}")

        # Contexto simple
        context = {
            'paciente': paciente,
            'consultas': consultas,
            'fecha_actual': timezone.now().date(),
        }

        # 1. PRIMERO: Probar si el template funciona
        html_string = render_to_string('doctores/pdf/historial_completo.html', context)
        print(f"✅ HTML generado correctamente ({len(html_string)} chars)")

        # 2. INTENTAR CON WEASYPRINT
        try:
            from weasyprint import HTML
            html = HTML(string=html_string)
            pdf_bytes = html.write_pdf()
            print(f"✅ PDF generado con WeasyPrint ({len(pdf_bytes)} bytes)")

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"historial_{paciente.dni}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except ImportError:
            print("⚠️ WeasyPrint no disponible, usando HTML como fallback")
            # Fallback: devolver HTML si no hay PDF
            response = HttpResponse(html_string, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="historial_{paciente.dni}.html"'
            return response

    except Exception as e:
        error_msg = f"Error al generar historial: {str(e)}"
        print(f"❌ {error_msg}")
        return HttpResponse(error_msg, status=500)

#####################

@login_required
@grupo_requerido('doctores')
def buscar_examenes_laboratorio_ajax(request):
    """Búsqueda AJAX para exámenes de laboratorio"""
    query = request.GET.get('q', '').strip()
    
    examenes = CatalogoExamen.objects.filter(
        tipo='LABORATORIO',
        activo=True,
        nombre__icontains=query
    ).order_by('nombre')[:10]
    
    resultados = [
        {
            'id': examen.id,
            'nombre': examen.nombre,
            'precio': str(examen.precio),
            'precio_formateado': examen.precio_formateado,
            'texto_completo': f"{examen.nombre} - S/ {examen.precio}"
        }
        for examen in examenes
    ]
    
    return JsonResponse({'resultados': resultados})


@login_required
@grupo_requerido('doctores')
def buscar_ecografias_ajax(request):
    """Búsqueda AJAX para ecografías"""
    query = request.GET.get('q', '').strip()
    
    ecografias = CatalogoEcografia.objects.filter(
        activo=True,
        nombre__icontains=query
    ).order_by('nombre')[:10]
    
    resultados = [
        {
            'id': eco.id,
            'nombre': eco.nombre,
            'precio': str(eco.precio),
            'precio_formateado': eco.precio_formateado,
            'texto_completo': f"{eco.nombre} - S/ {eco.precio}"
        }
        for eco in ecografias
    ]
    
    return JsonResponse({'resultados': resultados})


#################################

# doctores/views.py - AGREGAR ESTA FUNCIÓN AL FINAL (después de buscar_ecografias_ajax)

@login_required
@grupo_requerido('doctores')
def guardar_diagnostico_tratamiento_ajax(request, consulta_id):
    """
    Guardar automáticamente diagnóstico, observaciones y tratamiento usando AJAX
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            consulta = get_object_or_404(Consulta, id=consulta_id)

            # Verificar que el doctor es el dueño de esta consulta
            if consulta.doctor != request.user.doctor:
                return JsonResponse({
                    'success': False,
                    'error': 'No tiene permiso para modificar esta consulta'
                }, status=403)

            # Obtener datos del POST
            data = json.loads(request.body)

            diagnostico = data.get('diagnostico', '').strip()
            observaciones = data.get('observaciones', '').strip()
            tratamiento = data.get('tratamiento', '').strip()

            print(f"[DEBUG] Guardando para consulta {consulta_id}:")
            print(f"  Diagnóstico: {diagnostico[:50]}...")
            print(f"  Observaciones: {observaciones[:50]}...")
            print(f"  Tratamiento: {tratamiento[:50]}...")

            # Actualizar los campos
            actualizados = []

            if 'diagnostico' in data:
                consulta.diagnostico = diagnostico
                actualizados.append('diagnóstico')

            if 'observaciones' in data:
                consulta.observaciones = observaciones
                actualizados.append('observaciones')

            if 'tratamiento' in data:
                consulta.tratamiento = tratamiento
                actualizados.append('tratamiento')

            # Guardar en la base de datos
            consulta.save()

            return JsonResponse({
                'success': True,
                'message': f"Campos guardados: {', '.join(actualizados)}",
                'consulta_id': consulta_id,
                'timestamp': timezone.now().isoformat()
            })

        except Exception as e:
            print(f"[ERROR] al guardar diagnóstico: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


###################
@login_required
@grupo_requerido('doctores', 'administrador')
def ver_resultado_examen(request, examen_id):
    """
    Vista para que el doctor vea el resultado de un examen
    """
    from consultas.models import OrdenExamen

    examen = get_object_or_404(OrdenExamen, id=examen_id)

    # Verificar que el doctor tiene acceso a este paciente
    if examen.consulta and examen.consulta.doctor != request.user.doctor:
        messages.error(request, 'No tiene permiso para ver este resultado')
        return redirect('doctor_consultas')

    # Usar la misma plantilla de impresión pero sin botones de edición
    template_name = 'consultas/laboratorio/formatos/imprimir_generico.html'

    context = {
        'orden': examen,
        'resultados': examen.get_resultados_formateados(),
        'modo_impresion': True,
        'es_doctor': True,  # Para personalizar vista si es necesario
    }

    return render(request, template_name, context)

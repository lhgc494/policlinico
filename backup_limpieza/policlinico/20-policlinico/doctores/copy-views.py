from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from pacientes.models import Paciente
from triaje.models import Triaje
from consultas.forms import RecetaForm  # ← Agregar import
from consultas.models import Consulta, Receta  # ← Agregar Receta
from django.db.models import Q 
from django.http import HttpResponseForbidden
from consultas.forms import RecetaForm, OrdenExamenForm  # ← Agregar
from consultas.models import Consulta, Receta, OrdenExamen



####### buscar historial ########

@login_required
def buscar_historial(request):
    """
    Vista para buscar pacientes y ver su historial
    """
    query = request.GET.get('q', '')
    pacientes = None

    if query:
        # Buscar pacientes por DNI, nombre o apellido
        pacientes = Paciente.objects.filter(
            Q(dni__icontains=query) |
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query)
        ).order_by('apellidos', 'nombres')[:10]  # Limitar a 10 resultados

    return render(request, 'doctores/buscar_historial.html', {
        'pacientes': pacientes,
        'query': query
    })


######listado consultas##########
@login_required
def lista_consultas(request):
    """
    Vista para que el doctor vea sus consultas asignadas
    """
    try:
        doctor = request.user.doctor
        
        # Obtener filtro de estado (si existe)
        filtro_estado = request.GET.get('estado', 'pendientes')
        
        # Consultas base del doctor
        consultas = Consulta.objects.filter(doctor=doctor)
        
        # Aplicar filtro según parámetro
        if filtro_estado == 'pendientes':
            consultas = consultas.filter(estado='TRIAJE_COMPLETO')
        elif filtro_estado == 'atendidas':
            consultas = consultas.filter(estado='ATENDIDA')
        # Si es 'todas' no aplica filtro
        
        # Ordenar por fecha descendente
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

######################

@login_required
def atender_consulta(request, consulta_id):
    """
    Vista para que el doctor atienda una consulta
    """
    # Obtener la consulta
    consulta = get_object_or_404(
        Consulta, 
        id=consulta_id,
        doctor=request.user.doctor
    )
    
    # Obtener datos del triaje
    try:
        triaje = Triaje.objects.get(consulta=consulta)
    except Triaje.DoesNotExist:
        triaje = None
    
    # Obtener recetas existentes
    recetas_existentes = Receta.objects.filter(consulta=consulta)
    
    # Obtener órdenes de examen existentes
    ordenes_examen = OrdenExamen.objects.filter(consulta=consulta)
    
    if request.method == 'POST':
        # Verificar qué formulario se envió
        if 'finalizar_atencion' in request.POST:
            # Formulario de atención médica
            consulta.diagnostico = request.POST.get('diagnostico', '')
            consulta.observaciones = request.POST.get('observaciones', '')
            consulta.tratamiento = request.POST.get('tratamiento', '')
            consulta.estado = 'ATENDIDA'
            consulta.fecha_atencion = timezone.now()
            consulta.save()
            return redirect('doctor_consultas')
        
        elif 'agregar_receta' in request.POST:
            # Formulario de receta
            form_receta = RecetaForm(request.POST)
            if form_receta.is_valid():
                receta = form_receta.save(commit=False)
                receta.consulta = consulta
                receta.save()
                return redirect('atender_consulta', consulta_id=consulta_id)
        
        elif 'agregar_orden_examen' in request.POST:
            # Formulario de orden de examen
            form_orden = OrdenExamenForm(request.POST)
            if form_orden.is_valid():
                orden = form_orden.save(commit=False)
                orden.consulta = consulta
                orden.save()
                return redirect('atender_consulta', consulta_id=consulta_id)
    
    # Si es GET, mostrar formularios
    form_receta = RecetaForm()
    form_orden_examen = OrdenExamenForm()
    
    return render(request, 'doctores/atender_consulta.html', {
        'consulta': consulta,
        'paciente': consulta.paciente,
        'triaje': triaje,
        'recetas': recetas_existentes,
        'ordenes_examen': ordenes_examen,
        'form_receta': form_receta,
        'form_orden_examen': form_orden_examen
    })

##### historial paciente####
@login_required
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

    # Obtener todos los triajes de estas consultas
    triajes = Triaje.objects.filter(consulta__in=consultas)

    return render(request, 'doctores/historial_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'recetas': recetas,
        'triajes': triajes,
    })

#########
@login_required
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
            # Redirigir de vuelta a la atención de la consulta
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
    
    return render(request, 'doctores/editar_orden_examen.html', {
        'form': form,
        'orden': orden,
        'consulta': orden.consulta,
        'paciente': orden.consulta.paciente
    })

@login_required
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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .models import Triaje
from .forms import TriajeForm, EditarTriajeForm
from consultas.models import Consulta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from config.decorators import grupo_requerido

@grupo_requerido('recepcion', 'administrador')
@login_required
def crear_triaje(request, consulta_id):
    """
    Crear o completar un triaje para una consulta.
    - Marca la consulta como EN_TRIAGE al iniciar
    - Al completar todos los campos, el modelo automáticamente:
        1. Cambia triaje a estado COMPLETO
        2. Cambia consulta a estado TRIAJE_COMPLETO
    - NO marca como ATENDIDA (eso lo hace el médico después)
    """
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

            messages.success(request, 'Triaje registrado correctamente.')
            return redirect('lista_triaje_pendiente')
        else:
            print("Errores del formulario:", form.errors)
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = TriajeForm(instance=triaje)

    return render(request, 'triaje/triaje_form.html', {
        'form': form,
        'consulta': consulta
    })
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

####
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
        messages.warning(request, 'Solo se pueden editar triajes completados.')
        return redirect('historial_triajes')

    if request.method == 'POST':
        form = EditarTriajeForm(request.POST, instance=triaje)
        if form.is_valid():
            try:
                # Usar el método save() del formulario que usa update() directo
                form.save(triaje_id)
                messages.success(request, 'Triaje actualizado correctamente.')
                return redirect('historial_triajes')
            except Exception as e:
                print(f"Error al guardar: {e}")
                messages.error(request, f'Error al guardar: {str(e)}')
        else:
            # Mostrar errores detallados
            print("=" * 50)
            print(f"ERRORES EN FORMULARIO - Triaje #{triaje_id}")
            print("=" * 50)
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"{field}: {error}")
            print("=" * 50)
            
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EditarTriajeForm(instance=triaje)

    return render(request, 'triaje/editar_triaje.html', {
        'form': form,
        'triaje': triaje
    })

#####

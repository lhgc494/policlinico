from django.shortcuts import render, redirect, get_object_or_404
from .forms import PacienteForm
from .models import Paciente
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from config.decorators import grupo_requerido
from doctores.models import Doctor  # Importar al inicio

@login_required
def admin_dashboard(request):
    """Dashboard especial para administradores"""
    # Verificar que sea administrador
    if not request.user.groups.filter(name='administrador').exists() and not request.user.is_superuser:
        messages.error(request, 'Acceso restringido a administradores')
        return redirect('lista_pacientes')
    
    from datetime import date
    
    # Obtener todos los doctores activos para el filtro
    doctores = Doctor.objects.filter(activo=True).select_related('usuario').order_by('apellidos', 'nombres')
    
    # Fecha actual para el input date
    hoy = date.today().isoformat()
    
    context = {
        'titulo': 'Panel de Administración',
        'doctores': doctores,  # 👈 ESTO ES LO QUE FALTABA
        'hoy': hoy,
    }
    return render(request, 'admin_dashboard.html', context)

####### inicio ########
def inicio(request):
    """Redirección inteligente según tipo de usuario"""
    if request.user.is_authenticated:
        # 1. Si está en grupo "farmacia" → RECETAS PENDIENTES
        if request.user.groups.filter(name='farmacia').exists():
            return redirect('farmacia:recetas_pendientes')
        
        # 2. Si está en grupo "laboratorio" → ÓRDENES DE LABORATORIO (¡CORREGIDO!)
        if request.user.groups.filter(name='laboratorio').exists():
            return redirect('lista_ordenes_pendientes')  # ← ÚNICA redirección para laboratorio

        # 3. Si es doctor → sus consultas
        try:
            if hasattr(request.user, 'doctor') and request.user.doctor:
                return redirect('doctor_consultas')
        except:
            pass

        # 4. Si está en grupo "doctores" pero no tiene doctor asociado
        if request.user.groups.filter(name='doctores').exists():
            return redirect('doctor_consultas')

        # 5. Si está en grupo "recepcion" → recepción
        if request.user.groups.filter(name='recepcion').exists():
            return redirect('lista_pacientes')

        # 6. Si está en grupo "administrador" → DASHBOARD ADMIN
        if request.user.groups.filter(name='administrador').exists():
            return redirect('admin_dashboard')

        # 7. Para otros usuarios sin grupo → redirigir a login
        return redirect('login')

    # Usuario NO autenticado → página de login
    return render(request, 'login.html')

########################
@never_cache
def custom_logout(request):
    """
    Cierra sesión y redirige al login personalizado
    """
    # 1. Limpiar la sesión completamente
    request.session.flush()

    # 2. Eliminar todas las variables de sesión
    for key in list(request.session.keys()):
        del request.session[key]

    # 3. Cerrar sesión en el sistema de autenticación
    logout(request)

    # 4. Crear una nueva sesión vacía (para evitar errores)
    request.session.create()

    # 5. Redirigir al login con un parámetro para evitar cache
    response = redirect('login')

    # 6. Agregar headers anti-cache explícitamente
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response
######## crear paciente
@grupo_requerido('recepcion', 'administrador')
@never_cache
@login_required
def crear_paciente(request):
    """Crear nuevo paciente - Solo para recepción y administradores"""
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            try:
                paciente = form.save()

                # Mensaje de éxito
                messages.success(
                    request,
                    f'✅ Paciente registrado exitosamente: {paciente.nombres} {paciente.apellidos}'
                )

                # Verificar qué acción se solicitó
                if 'guardar_y_crear_consulta' in request.POST:
                    # Redirigir a crear consulta para este paciente
                    return redirect('crear_consulta', paciente_id=paciente.id)
                else:
                    # Redirigir a la lista de pacientes
                    return redirect('lista_pacientes')

            except Exception as e:
                # Manejar cualquier error inesperado (excepciones del sistema)
                messages.error(
                    request,
                    f'❌ Error al guardar el paciente: {str(e)}'
                )
        else:
            # === SOLO PARA DEBUG EN CONSOLA (OPCIONAL) ===
            # print("=" * 60)
            # print("🔍 ERRORES DE VALIDACIÓN (solo consola):")
            # for field_name, errors in form.errors.items():
            #     print(f"  {field_name}: {errors}")
            # print("=" * 60)
            # === FIN DEBUG ===
            
            # NO ENVIAR MENSAJES DE ERROR - Se muestran en el template
            pass
    else:
        form = PacienteForm()

    return render(request, 'pacientes/crear_paciente.html', {
        'form': form,
        'titulo': 'Registro de Nuevo Paciente'
    })

############### listado pacientes
@grupo_requerido('recepcion', 'administrador')
@never_cache
@login_required
def lista_pacientes(request):
    """Lista de pacientes - Solo para recepción y administradores"""
    query = request.GET.get('q', '')

    # QUITAR filtro por estado activo - Mostrar TODOS los pacientes
    pacientes_qs = Paciente.objects.all()

    # Ordenar por apellidos, nombres
    pacientes_qs = pacientes_qs.order_by('apellidos', 'nombres')

    # Búsqueda (sin email - ya corregido)
    if query:
        pacientes_qs = pacientes_qs.filter(
            Q(dni__icontains=query) |
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(telefono__icontains=query)
        )

    paginator = Paginator(pacientes_qs, 10)
    page_number = request.GET.get('page')
    pacientes = paginator.get_page(page_number)

    return render(request, 'pacientes/lista_pacientes.html', {
        'pacientes': pacientes,
        'query': query,
        'total_pacientes': pacientes_qs.count(),
    })


##########editar paciente########
@grupo_requerido('recepcion', 'administrador')
@never_cache
@login_required
def editar_paciente(request, paciente_id):
    """Editar paciente - Solo para recepción y administradores"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request,
                    f'✅ Paciente actualizado: {paciente.nombres} {paciente.apellidos}'
                )
                return redirect('lista_pacientes')
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error al actualizar paciente: {str(e)}'
                )
        else:
            # === SOLO PARA DEBUG EN CONSOLA (OPCIONAL) ===
            # print("=" * 60)
            # print("🔍 ERRORES DE VALIDACIÓN (solo consola):")
            # for field_name, errors in form.errors.items():
            #     print(f"  {field_name}: {errors}")
            # print("=" * 60)
            # === FIN DEBUG ===
            
            # NO ENVIAR MENSAJES DE ERROR - Se muestran en el template
            pass
    else:
        form = PacienteForm(instance=paciente)

    return render(request, 'pacientes/editar_paciente.html', {
        'form': form,
        'paciente': paciente,
        'titulo': f'Editar Paciente: {paciente.nombres} {paciente.apellidos}'
    })

################
@grupo_requerido('recepcion', 'administrador')
@never_cache
@login_required
def eliminar_paciente(request, paciente_id):
    """Eliminar paciente - Solo para recepción y administradores"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    if request.method == 'POST':
        try:
            # Marcar como inactivo en lugar de eliminar físicamente
            paciente.activo = False
            paciente.save()
            
            messages.success(
                request,
                f'✅ Paciente marcado como inactivo: {paciente.nombres} {paciente.apellidos}'
            )
            return redirect('lista_pacientes')
        except Exception as e:
            messages.error(
                request,
                f'❌ Error al desactivar paciente: {str(e)}'
            )
            return redirect('lista_pacientes')

    return render(request, 'pacientes/confirmar_eliminar.html', {
        'paciente': paciente,
        'titulo': f'Desactivar Paciente: {paciente.nombres} {paciente.apellidos}'
    })

@grupo_requerido('recepcion', 'administrador', 'doctores')
@never_cache
@login_required
def detalle_paciente(request, paciente_id):
    """Detalle del paciente - Para recepción, administradores y doctores"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    
    # Obtener consultas del paciente (si existen)
    consultas = []
    if hasattr(paciente, 'consultas'):
        consultas = paciente.consultas.all().order_by('-fecha_consulta')[:5]
    
    return render(request, 'pacientes/detalle_paciente.html', {
        'paciente': paciente,
        'consultas': consultas,
        'titulo': f'Detalle del Paciente: {paciente.nombres} {paciente.apellidos}'
    })

@grupo_requerido('recepcion', 'administrador')
@never_cache
@login_required
def activar_paciente(request, paciente_id):
    """Reactivar un paciente previamente desactivado"""
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    
    if not paciente.activo:
        paciente.activo = True
        paciente.save()
        messages.success(
            request,
            f'✅ Paciente reactivado: {paciente.nombres} {paciente.apellidos}'
        )
    
    return redirect('lista_pacientes')

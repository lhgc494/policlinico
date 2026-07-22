# Al inicio del archivo
from consultas.models import CatalogoExamen, CatalogoEcografia, OrdenExamen
from datetime import timedelta
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
from .models import CatalogoExamen
from django.db.models import Q
from .models import (
    Consulta,
    Receta,
    OrdenExamen,
    CatalogoExamen,
    VentaAmbulatoria
)

##########################
# FUNCIONES AUXILIARES
##########################

def calcular_estadisticas_ordenes():
    """
    Calcula estadísticas CORRECTAS para órdenes de laboratorio.
    SIN contar urgentes (según requerimiento).
    """
    # Obtener todas las órdenes de laboratorio pendientes
    ordenes_pendientes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='SOLICITADO'
    )

    # Calcular contadores REALES (sin urgentes)
    stats = {
        'total_pendientes': ordenes_pendientes.count(),
        'internos': 0,
        'ambulatorios': 0,
    }

    # Calcular usando Python
    for orden in ordenes_pendientes:
        if orden.consulta:
            stats['internos'] += 1
        else:
            stats['ambulatorios'] += 1

    return stats

def get_contadores_ordenes():
    """Obtiene contadores para todos los estados"""
    return {
        'pendientes_count': OrdenExamen.objects.filter(
            tipo_examen='LABORATORIO',
            estado='SOLICITADO'
        ).count(),
        'en_proceso_count': OrdenExamen.objects.filter(
            tipo_examen='LABORATORIO',
            estado='EN_PROCESO'
        ).count(),
        'completadas_count': OrdenExamen.objects.filter(
            tipo_examen='LABORATORIO',
            estado='COMPLETADO'
        ).count(),
        'entregadas_count': OrdenExamen.objects.filter(
            tipo_examen='LABORATORIO',
            estado='ENTREGADO'
        ).count(),
    }

def es_laboratorio(user):
    """Verifica si el usuario pertenece al grupo laboratorio"""
    return user.groups.filter(name='laboratorio').exists()

def obtener_mis_ordenes_simplificado(user):
    """
    Obtiene mis órdenes en proceso SIN información de urgente/prioridad/tiempo
    según requerimiento 5.
    """
    # Solo órdenes asignadas al usuario actual
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='EN_PROCESO',
        tecnico_asignado=user
    ).select_related(
        'consulta__paciente',
        'consulta__doctor__usuario',
        'venta_ambulatoria'
    ).order_by('fecha_asignacion')

    # NO contamos urgentes, NO calculamos tiempos
    stats = {
        'total': ordenes.count(),
        'internos': ordenes.filter(consulta__isnull=False).count(),
        'ambulatorios': ordenes.filter(consulta__isnull=True).count(),
    }

    return ordenes, stats

# ==============================================
# VISTAS PARA LABORATORIO
# ==============================================
@login_required
@user_passes_test(es_laboratorio)
def lista_ordenes_pendientes(request):
    """
    Vista para órdenes pendientes - CON ESTADO DE PAGO CORREGIDO
    """
    # 1. Órdenes pendientes
    ordenes_pendientes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='SOLICITADO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    ).order_by('fecha_solicitud')

    # ✅ CORRECCIÓN: Determinar estado de pago para cada orden CON MANEJO DE None
    for orden in ordenes_pendientes:
        # ✅ SOLUCIÓN CRÍTICA: Asegurar que pagado no sea None
        if orden.pagado is None:
            orden.pagado = False
        
        if orden.consulta is None:  # Es ambulatorio
            orden.estado_pago_display = '✅ Pagado'
            orden.puede_cobrar = False
            orden.es_pagado = True
        else:  # Es interno
            if orden.pagado:  # Ya pagó
                orden.estado_pago_display = '✅ Pagado'
                orden.puede_cobrar = False
                orden.es_pagado = True
            else:  # No ha pagado
                orden.estado_pago_display = '❌ Por Cobrar'
                orden.puede_cobrar = True
                orden.es_pagado = False

    # 2. Órdenes para las otras pestañas
    ordenes_en_proceso = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='EN_PROCESO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    ).order_by('-fecha_asignacion')

    ordenes_completados = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='COMPLETADO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    ).order_by('-fecha_realizacion')

    ordenes_entregados = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='ENTREGADO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    ).order_by('-fecha_entrega')

    # 3. Calcular estadísticas
    stats = calcular_estadisticas_ordenes()
    contadores = get_contadores_ordenes()

    # 4. Contexto COMPLETO
    context = {
        # Variables principales
        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_en_proceso': ordenes_en_proceso,
        'ordenes_completados': ordenes_completados,
        'ordenes_entregados': ordenes_entregados,

        'titulo': 'Pendientes',
        'es_laboratorio': True,

        # Estadísticas
        'internos_count': stats['internos'],
        'ambulatorios_count': stats['ambulatorios'],
        'total_pendientes': stats['total_pendientes'],

        # Contadores
        'pendientes_count': contadores.get('pendientes_count', 0),
        'en_proceso_count': contadores.get('en_proceso_count', 0),
        'completadas_count': contadores.get('completadas_count', 0),
        'entregadas_count': contadores.get('entregadas_count', 0),

        # Para búsqueda de entregados (si aplica)
        'dni_busqueda': request.GET.get('dni', ''),
    }

    return render(request, 'consultas/laboratorio/lista_ordenes.html', context)

######################################
@login_required
@user_passes_test(es_laboratorio)
def mis_ordenes_en_proceso(request):
    """
    Muestra solo las órdenes asignadas AL USUARIO ACTUAL
    """
    # Órdenes de consulta (internos) en proceso
    ordenes_internos = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='EN_PROCESO',
        tecnico_asignado=request.user,
        consulta__isnull=False
    ).select_related(
        'consulta__paciente',
        'consulta__doctor__usuario'
    ).order_by('fecha_solicitud')

    # Órdenes ambulatorias en proceso
    ordenes_ambulatorios = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='EN_PROCESO',
        tecnico_asignado=request.user,
        consulta__isnull=True,
        venta_ambulatoria__isnull=False
    ).select_related('venta_ambulatoria').order_by('fecha_solicitud')

    # Combinar ambas listas
    ordenes = list(ordenes_internos) + list(ordenes_ambulatorios)

    # Contar órdenes urgentes
    ordenes_urgentes_count = sum(1 for orden in ordenes if orden.urgente)

    context = {
        'ordenes': ordenes,
        'ordenes_internos_count': len(ordenes_internos),
        'ordenes_ambulatorios_count': len(ordenes_ambulatorios),
        'ordenes_urgentes_count': ordenes_urgentes_count,
        'es_laboratorio': True,
        **get_contadores_ordenes(),
    }

    return render(request, 'consultas/laboratorio/mis_ordenes.html', context)

@login_required
@user_passes_test(es_laboratorio)
def ordenes_en_proceso(request):
    """Órdenes en estado EN_PROCESO (para todos los técnicos)"""
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='EN_PROCESO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria',
        'tecnico_asignado'
    ).order_by('-fecha_asignacion')

    contadores = get_contadores_ordenes()
    
    context = {
        'ordenes_en_proceso': ordenes,  # ¡IMPORTANTE! Nombre correcto
        'titulo': 'En Proceso',
        'es_laboratorio': True,
        **contadores,
    }

    return render(request, 'consultas/laboratorio/lista_ordenes.html', context)

@login_required
@user_passes_test(es_laboratorio)
def ordenes_completadas(request):
    """Órdenes en estado COMPLETADO"""
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='COMPLETADO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria',
        'tecnico_asignado'
    ).order_by('-fecha_realizacion')

    contadores = get_contadores_ordenes()
    
    # Calcular estadísticas adicionales
    total_completados = ordenes.count()
    internos_completados = ordenes.filter(consulta__isnull=False).count()
    ambulatorios_completados = ordenes.filter(consulta__isnull=True).count()
    
    # Completados hoy
    hoy = timezone.now().date()
    completados_hoy = ordenes.filter(fecha_realizacion__date=hoy).count()

    context = {
        'ordenes_completados': ordenes,  # ¡IMPORTANTE! Nombre correcto (PLURAL)
        'titulo': 'Completadas',
        'es_laboratorio': True,
        'total_completados': total_completados,
        'internos_completados': internos_completados,
        'ambulatorios_completados': ambulatorios_completados,
        'completados_hoy': completados_hoy,
        **contadores,
    }

    return render(request, 'consultas/laboratorio/lista_ordenes.html', context)
###############################
# En views.py, reemplaza la función ordenes_entregadas con:
@login_required
@user_passes_test(es_laboratorio)
def ordenes_entregadas(request):
    """Órdenes en estado ENTREGADO - VERSIÓN SIMPLE"""
    # Solo obtener órdenes entregadas
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO',
        estado='ENTREGADO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    ).order_by('-fecha_entrega')
    
    # Paginación simple
    from django.core.paginator import Paginator
    paginator = Paginator(ordenes, 15)  # 15 por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Contadores simples (solo para badges de tabs)
    contadores = get_contadores_ordenes()
    
    context = {
        'ordenes_entregados': page_obj,
        'page_obj': page_obj,
        'titulo': 'Entregadas',
        
        # Solo contadores necesarios para badges
        'pendientes_count': contadores.get('pendientes_count', 0),
        'en_proceso_count': contadores.get('en_proceso_count', 0),
        'completadas_count': contadores.get('completadas_count', 0),
        'entregadas_count': contadores.get('entregadas_count', 0),
    }
    
    return render(request, 'consultas/laboratorio/lista_ordenes.html', context)

##################
@login_required
@user_passes_test(es_laboratorio)
def asignar_orden(request, orden_id):
    """Asignar una orden específica al laboratorista actual"""
    print(f"\n{'='*50}")
    print(f"DEBUG ASIGNAR_ORDEN - Orden #{orden_id}")
    
    orden = get_object_or_404(OrdenExamen, id=orden_id)
    
    # DEBUG
    print(f"Estado: {orden.estado}")
    print(f"Técnico asignado: {orden.tecnico_asignado}")
    print(f"Pagado: {orden.pagado}")
    print(f"Es interno: {orden.consulta is not None}")
    
    # VALIDACIONES MEJORADAS
    if orden.tipo_examen != 'LABORATORIO':
        print("❌ No es laboratorio")
        messages.error(request, '❌ Solo se pueden asignar órdenes de Laboratorio.')
        return redirect('lista_ordenes_pendientes')

    if orden.estado != 'SOLICITADO':
        print(f"❌ Estado incorrecto: {orden.estado}")
        estado_actual = orden.get_estado_display()
        messages.error(request, f'❌ La orden ya está {estado_actual.lower()}.')
        return redirect('lista_ordenes_pendientes')

    if orden.tecnico_asignado:
        print(f"❌ Ya tiene técnico: {orden.tecnico_asignado}")
        tecnico = orden.tecnico_asignado.get_full_name() or orden.tecnico_asignado.username
        messages.warning(request, f'⚠️ Ya está asignada a: {tecnico}')
        return redirect('lista_ordenes_pendientes')

    # ✅ NUEVA VALIDACIÓN: Si es INTERNA, debe estar PAGADA
    if orden.consulta and not orden.pagado:
        print(f"❌ Orden interna no pagada")
        messages.error(request, '❌ Primero debe cobrar la orden interna antes de asignarla.')
        return redirect('lista_ordenes_pendientes')

    # ASIGNAR
    print("✅ Validaciones OK - Asignando...")
    orden.estado = 'EN_PROCESO'
    orden.tecnico_asignado = request.user
    orden.fecha_asignacion = timezone.now()
    orden.save()
    
    print(f"✅ Orden #{orden.id} asignada a {request.user.username}")
    print(f"{'='*50}\n")
    
    user_name = request.user.get_full_name() or request.user.username
    messages.success(request, f'✅ Orden #{orden.id} asignada a: {user_name}')

    return redirect('mis_ordenes_en_proceso')
##################
@login_required
@user_passes_test(es_laboratorio)
def detalle_orden_examen(request, orden_id):
    """
    Vista CORREGIDA para ver detalles de una orden de examen
    """
    orden = get_object_or_404(
        OrdenExamen.objects.select_related(
            'consulta__paciente',
            'consulta__doctor',
            'venta_ambulatoria'
        ),
        id=orden_id,
        tipo_examen='LABORATORIO'
    )

    es_ambulatoria = orden.consulta is None and orden.venta_ambulatoria is not None

    # ✅ NUEVO: Verificar si la orden se puede asignar
    puede_asignarse = (
        orden.estado == 'SOLICITADO' and 
        not orden.pagado and  # ← ¡IMPORTANTE! Verificar que NO esté pagada
        not orden.tecnico_asignado
    )
    
    # ✅ NUEVO: Motivo por el que no se puede asignar
    motivo_no_asignable = ""
    if orden.pagado:
        motivo_no_asignable = "Por pagar - Complete el pago primero"
    elif orden.tecnico_asignado:
        motivo_no_asignable = f"Ya asignada a {orden.tecnico_asignado.get_full_name()}"
    elif orden.estado != 'SOLICITADO':
        motivo_no_asignable = f"Estado actual: {orden.get_estado_display()}"

    # PREPARAR DATOS DEL PACIENTE (código existente sin cambios)
    paciente_data = {}
    if es_ambulatoria:
        venta = orden.venta_ambulatoria
        paciente_data = {
            'nombres': venta.paciente_nombre if venta else 'N/A',
            'apellidos': '',
            'nombre_completo': venta.paciente_nombre if venta else 'N/A',
            'dni': venta.paciente_dni if venta else 'N/A',
            'edad': 'No disponible',
            'telefono': 'No disponible',
            'es_ambulatorio': True,
        }
    else:
        if orden.consulta and orden.consulta.paciente:
            paciente = orden.consulta.paciente

            edad_info = 'N/A'
            try:
                if hasattr(paciente, 'get_edad'):
                    edad_info = paciente.get_edad()
                elif hasattr(paciente, 'edad'):
                    edad_val = paciente.edad
                    if callable(edad_val):
                        edad_info = edad_val()
                    else:
                        edad_info = str(edad_val)
            except:
                edad_info = 'N/A'

            telefono_info = 'No registrado'
            try:
                if hasattr(paciente, 'telefono'):
                    telefono = paciente.telefono
                    if telefono:
                        telefono_info = telefono
            except:
                telefono_info = 'No registrado'

            paciente_data = {
                'nombres': paciente.nombres if hasattr(paciente, 'nombres') else 'N/A',
                'apellidos': paciente.apellidos if hasattr(paciente, 'apellidos') else '',
                'nombre_completo': f"{paciente.nombres} {paciente.apellidos}".strip() if hasattr(paciente, 'nombres') else 'N/A',
                'dni': paciente.dni if hasattr(paciente, 'dni') else 'N/A',
                'edad': edad_info,
                'telefono': telefono_info,
                'es_ambulatorio': False,
            }
        else:
            paciente_data = {
                'nombres': 'N/A',
                'apellidos': '',
                'nombre_completo': 'Datos no disponibles',
                'dni': 'N/A',
                'edad': 'N/A',
                'telefono': 'No disponible',
                'es_ambulatorio': False,
            }

    # MANEJO DE PETICIONES POST (código existente sin cambios)
    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'completar':
            orden.estado = 'COMPLETADO'
            orden.fecha_realizacion = timezone.now()
            orden.save()
            messages.success(request, f'✅ Orden #{orden.id} marcada como completada')
            return redirect('ordenes_completadas')

        elif accion == 'entregar':
            orden.estado = 'ENTREGADO'
            orden.fecha_entrega = timezone.now()
            orden.save()
            messages.success(request, f'✅ Orden #{orden.id} marcada como entregada')
            return redirect('ordenes_entregadas')

        return redirect('detalle_orden_examen', orden_id=orden.id)

    context = {
        'orden': orden,
        'paciente': paciente_data,
        'consulta': orden.consulta,
        'es_ambulatoria': es_ambulatoria,
        'es_laboratorio': True,
        'puede_asignarse': puede_asignarse,  # ← NUEVO
        'motivo_no_asignable': motivo_no_asignable,  # ← NUEVO
    }

    return render(request, 'consultas/laboratorio/detalle_orden.html', context)

##################
@login_required
@user_passes_test(es_laboratorio)
def cancelar_orden(request, orden_id):
    """
    Cancelar una orden en estado SOLICITADO
    """
    orden = get_object_or_404(OrdenExamen, id=orden_id)

    if orden.estado != 'SOLICITADO':
        messages.error(request, f'❌ Solo se pueden cancelar órdenes en estado "Solicitado". Esta orden ya está {orden.get_estado_display()}.')
        return redirect('lista_ordenes_pendientes')

    orden_id = orden.id
    paciente_nombre = ""

    if orden.consulta:
        paciente_nombre = f"{orden.consulta.paciente.nombres} {orden.consulta.paciente.apellidos}"
    elif orden.venta_ambulatoria:
        paciente_nombre = orden.venta_ambulatoria.paciente_nombre

    orden.delete()

    messages.success(request, f'✅ Orden #{orden_id} cancelada exitosamente. Paciente: {paciente_nombre}')
    return redirect('lista_ordenes_pendientes')

# ==============================================
# VISTAS PARA PUNTO DE VENTA LABORATORIO
# ==============================================
@login_required
@user_passes_test(es_laboratorio)
def punto_venta_laboratorio(request):
    examenes = CatalogoExamen.objects.filter(
        activo=True,
        tipo='LABORATORIO'
    ).order_by('nombre')

    carrito = request.session.get('carrito_laboratorio', {})
    
    # NUEVO: Calcular tipos en el carrito
    tiene_examenes_nuevos = False
    tiene_ordenes_internas = False
    
    for item in carrito.values():
        if item.get('tipo') == 'INTERNO_POR_COBRAR':
            tiene_ordenes_internas = True
        else:
            tiene_examenes_nuevos = True
    
    total = Decimal('0.00')
    for item in carrito.values():
        total += Decimal(item['precio']) * item['cantidad']

    context = {
        'examenes': examenes,
        'carrito': carrito,
        'total_carrito': total,
        'items_carrito': len(carrito),
        # NUEVAS VARIABLES:
        'tiene_examenes_nuevos': tiene_examenes_nuevos,
        'tiene_ordenes_internas': tiene_ordenes_internas,
        'es_laboratorio': True,
    }

    return render(request, 'consultas/laboratorio/punto_venta.html', context)
################################################
@login_required
@user_passes_test(es_laboratorio)
def agregar_al_carrito(request, examen_id):
    """Agregar un examen al carrito - CON VALIDACIÓN DE NO MEZCLA"""
    
    # ✅ VALIDACIÓN SIMPLE: Si tiene órdenes internas, NO agregar examen nuevo
    carrito = request.session.get('carrito_laboratorio', {})
    tiene_ordenes_internas = any(k.startswith('orden_interna_') for k in carrito.keys())
    
    if tiene_ordenes_internas:
        messages.error(request, '❌ No puedes agregar exámenes nuevos porque ya tienes órdenes internas en el carrito.')
        return redirect('punto_venta_laboratorio')
    
    # RESTO DE TU CÓDIGO ORIGINAL (sin cambios)
    examen = get_object_or_404(CatalogoExamen, id=examen_id, activo=True)

    if 'carrito_laboratorio' not in request.session:
        request.session['carrito_laboratorio'] = {}

    carrito = request.session['carrito_laboratorio']

    if str(examen_id) in carrito:
        carrito[str(examen_id)]['cantidad'] += 1
    else:
        carrito[str(examen_id)] = {
            'id': examen.id,
            'nombre': examen.nombre,
            'tipo': examen.tipo,
            'precio': str(examen.precio),
            'cantidad': 1,
            'descripcion': examen.descripcion,
        }

    request.session.modified = True
    messages.success(request, f"✅ {examen.nombre} agregado al carrito")
    return redirect('punto_venta_laboratorio')

###################################
# Asegúrate que recibe 'item_id' (no 'examen_id')
def eliminar_del_carrito(request, item_id):  # <-- item_id, no examen_id
    """Elimina un item del carrito"""
    carrito = request.session.get('carrito_laboratorio', {})
    
    if str(item_id) in carrito:  # <-- Convertir a string por seguridad
        del carrito[str(item_id)]
        request.session['carrito_laboratorio'] = carrito
        messages.success(request, 'Item eliminado del carrito')
    
    return redirect('punto_venta_laboratorio')
##########################################################
@login_required
@user_passes_test(es_laboratorio)
def actualizar_cantidad(request, item_id):  # <-- CAMBIAR examen_id → item_id
    """Actualizar cantidad de un item en el carrito (examen nuevo O orden interna)"""
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        
        if cantidad < 1:
            cantidad = 1
        
        carrito = request.session.get('carrito_laboratorio', {})
        
        if str(item_id) in carrito:  # <-- item_id ya es string
            carrito[str(item_id)]['cantidad'] = cantidad
            request.session['carrito_laboratorio'] = carrito
            messages.success(request, 'Cantidad actualizada')
    
    return redirect('punto_venta_laboratorio')

###########
@login_required
@user_passes_test(es_laboratorio)
def limpiar_carrito(request):
    """Limpiar todo el carrito"""
    if 'carrito_laboratorio' in request.session:
        del request.session['carrito_laboratorio']
        request.session.modified = True
        messages.info(request, "🗑️ Carrito limpiado")

    return redirect('punto_venta_laboratorio')
#######################################
@login_required
@user_passes_test(es_laboratorio)
def procesar_venta_ambulatoria(request):
    """Procesa venta ambulatoria Y cobro de órdenes internas - VERSIÓN CON DESCUENTO PARA AMBOS"""
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

        # OBTENER DESCUENTO
        descuento_str = request.POST.get('descuento', '0').strip()
        descuento = Decimal(descuento_str) if descuento_str else Decimal('0')

        # Validar descuento
        if descuento < 0:
            descuento = Decimal('0')
            messages.warning(request, '⚠️ El descuento no puede ser negativo. Se estableció en 0.')

        carrito = request.session.get('carrito_laboratorio', {})

        if not carrito:
            messages.error(request, '❌ El carrito está vacío')
            return redirect('punto_venta_laboratorio')

        # SEPARAR ITEMS POR TIPO
        items_nuevos = [item for item in carrito.values() if item.get('tipo') != 'INTERNO_POR_COBRAR']
        items_por_cobrar = [item for item in carrito.values() if item.get('tipo') == 'INTERNO_POR_COBRAR']

        # VARIABLES PARA CALCULAR TOTALES
        total_nuevos = Decimal('0.00')
        total_internas = Decimal('0.00')
        total_sin_descuento = Decimal('0.00')  # Total antes de descuento
        ordenes_creadas = []
        ordenes_cobradas = []
        venta = None

        try:
            # 1. CALCULAR TOTALES ANTES DE PROCESAR
            # Calcular total para exámenes nuevos
            for item in items_nuevos:
                total_nuevos += Decimal(str(item['precio'])) * item['cantidad']
            
            # Calcular total para órdenes internas
            for item in items_por_cobrar:
                total_internas += Decimal(str(item['precio']))  # Solo 1 por orden interna
            
            total_sin_descuento = total_nuevos + total_internas
            
            # 2. VALIDAR Y APLICAR DESCUENTO
            porcentaje_descuento = Decimal('0')
            descuento_nuevos = Decimal('0')
            descuento_internas = Decimal('0')
            
            if descuento > 0:
                # No permitir descuento mayor al total
                if descuento > total_sin_descuento:
                    descuento = total_sin_descuento
                    messages.warning(request, f'⚠️ El descuento se ajustó a S/ {descuento:.2f} (no puede superar el total)')
                
                # Calcular porcentaje de descuento
                porcentaje_descuento = descuento / total_sin_descuento if total_sin_descuento > 0 else Decimal('0')
                
                # Aplicar descuento proporcionalmente
                descuento_nuevos = total_nuevos * porcentaje_descuento
                descuento_internas = total_internas * porcentaje_descuento
                
                total_nuevos -= descuento_nuevos
                total_internas -= descuento_internas
                
                print(f"[DEBUG PROCESAR] Descuento total: S/ {descuento:.2f}")
                print(f"[DEBUG PROCESAR] Descuento nuevos: S/ {descuento_nuevos:.2f}")
                print(f"[DEBUG PROCESAR] Descuento internas: S/ {descuento_internas:.2f}")
                print(f"[DEBUG PROCESAR] Total con descuento: S/ {(total_nuevos + total_internas):.2f}")

            # 3. PROCESAR EXÁMENES NUEVOS (AMBULATORIOS)
            if items_nuevos:
                if not dni or not nombre:
                    messages.error(request, '❌ Para exámenes nuevos debe ingresar DNI y nombre del paciente')
                    return redirect('punto_venta_laboratorio')

                # Crear venta primero
                venta = VentaAmbulatoria.objects.create(
                    paciente_dni=dni,
                    paciente_nombre=nombre,
                    total=float(total_nuevos + total_internas),  # Total CON descuento aplicado
                    descuento_aplicado=float(descuento),  # Descuento total aplicado
                    usuario=request.user
                )

                # Crear órdenes para exámenes nuevos
                for item in items_nuevos:
                    examen = CatalogoExamen.objects.get(id=item['id'])
                    precio_examen_original = Decimal(str(item['precio']))
                    
                    # Aplicar descuento proporcional a cada examen nuevo
                    factor_descuento = (Decimal('1') - porcentaje_descuento) if descuento > 0 else Decimal('1')
                    precio_examen_con_descuento = precio_examen_original * factor_descuento

                    for i in range(item['cantidad']):
                        orden_examen = OrdenExamen.objects.create(
                            consulta=None,
                            venta_ambulatoria=venta,
                            tipo_examen='LABORATORIO',
                            examen_especifico=examen.nombre,
                            indicaciones=(
                                f"PACIENTE EXTERNO (AMBULATORIO)\n"
                                f"Nombre: {nombre}\n"
                                f"DNI: {dni}\n"
                                f"Venta: #{venta.id}\n"
                                f"{'Observaciones: ' + observaciones if observaciones else ''}"
                            ),
                            estado='SOLICITADO',
                            pagado=True,
                            metodo_pago=metodo_pago,
                            monto_pagado=float(precio_examen_con_descuento),  # Precio con descuento
                            fecha_pago=timezone.now()
                        )
                        ordenes_creadas.append(orden_examen.id)

            # 4. PROCESAR ÓRDENES INTERNAS POR COBRAR
            if items_por_cobrar:
                for item in items_por_cobrar:
                    try:
                        orden = OrdenExamen.objects.get(id=item['orden_id'])
                        precio_original = Decimal(str(item['precio']))
                        
                        # Aplicar descuento proporcional a orden interna
                        if descuento > 0:
                            factor_descuento = (Decimal('1') - porcentaje_descuento)
                            precio_con_descuento = precio_original * factor_descuento
                        else:
                            precio_con_descuento = precio_original

                        # Marcar como pagada con precio con descuento
                        orden.pagado = True
                        orden.metodo_pago = metodo_pago
                        orden.monto_pagado = float(precio_con_descuento)  # Precio con descuento
                        orden.fecha_pago = timezone.now()
                        orden.save()

                        ordenes_cobradas.append({
                            'id': orden.id,
                            'examen': orden.examen_especifico,
                            'precio_original': float(precio_original),  # Precio original para el ticket
                            'precio': float(precio_con_descuento),  # Precio con descuento (para compatibilidad)
                            'precio_final': float(precio_con_descuento),  # Precio final con descuento
                            'descuento_aplicado': float(precio_original - precio_con_descuento),
                            'paciente': orden.get_paciente_nombre(),
                            'dni': orden.get_paciente_dni()
                        })

                    except OrdenExamen.DoesNotExist:
                        continue

                # Si solo hay órdenes internas (sin exámenes nuevos), crear venta para el ticket
                if not venta and ordenes_cobradas:
                    primer_orden = ordenes_cobradas[0]
                    
                    venta = VentaAmbulatoria.objects.create(
                        paciente_dni=primer_orden['dni'],
                        paciente_nombre=f"COBRO INTERNO - {primer_orden['paciente'][:30]}",
                        total=float(total_internas),  # Total de órdenes internas con descuento
                        descuento_aplicado=float(descuento_internas),
                        usuario=request.user
                    )

            # 5. LIMPIAR CARRITO
            if 'carrito_laboratorio' in request.session:
                del request.session['carrito_laboratorio']
            request.session.modified = True

            # 6. Preparar datos para sesión (IMPORTANTE: para ticket_cobro_interno)
            datos_cobro = {}
            if ordenes_cobradas:
                # Calcular el descuento que realmente se aplicó a las órdenes internas
                descuento_aplicado_internas = descuento_internas if items_por_cobrar else Decimal('0')
                
                datos_cobro = {
                    'ids': [oc['id'] for oc in ordenes_cobradas],
                    'detalles': ordenes_cobradas,
                    'total': float(total_sin_descuento),  # Total sin descuento
                    'descuento': float(descuento_aplicado_internas),  # Descuento aplicado a internas
                    'total_con_descuento': float(total_internas),  # Total con descuento (ya calculado)
                    'metodo_pago': metodo_pago,
                    'fecha': timezone.now().isoformat()
                }
                request.session['ultimas_ordenes_cobradas'] = datos_cobro
                request.session.modified = True
                
                print(f"[DEBUG PROCESAR] Descuento guardado en sesión: {descuento_aplicado_internas}")
                print(f"[DEBUG PROCESAR] Total guardado en sesión: {total_sin_descuento}")
                print(f"[DEBUG PROCESAR] Total con descuento guardado: {total_internas}")

            # 7. MENSAJE COMBINADO
            mensaje_parts = []

            if ordenes_creadas:
                mensaje_parts.append(f'📋 {len(ordenes_creadas)} orden(es) nueva(s) creada(s)')

            if ordenes_cobradas:
                mensaje_parts.append(f'💰 {len(ordenes_cobradas)} orden(es) interna(s) cobrada(s)')

            mensaje = '✅ ' + ' | '.join(mensaje_parts)
            mensaje += f'\n💵 Subtotal: S/ {total_sin_descuento:.2f}'

            if descuento > 0:
                mensaje += f'\n🎫 Descuento: S/ {descuento:.2f}'
                mensaje += f'\n💳 Total con descuento: S/ {(total_sin_descuento - descuento):.2f}'
            else:
                mensaje += f'\n💳 Total: S/ {total_sin_descuento:.2f}'

            messages.success(request, mensaje)

            # 8. REDIRIGIR SEGÚN QUÉ SE PROCESÓ
            if venta:
                if ordenes_creadas:
                    # Hay exámenes nuevos ambulatorios
                    return redirect('ticket_venta_ambulatoria', venta_id=venta.id)
                elif ordenes_cobradas:
                    # Solo órdenes internas cobradas
                    return redirect('ticket_cobro_interno', venta_id=venta.id)
            else:
                return redirect('lista_ordenes_pendientes')

        except CatalogoExamen.DoesNotExist as e:
            messages.error(request, f'❌ Error: Examen no encontrado en el catálogo')
            return redirect('punto_venta_laboratorio')
        except Exception as e:
            messages.error(request, f'❌ Error al procesar: {str(e)}')
            import traceback
            traceback.print_exc()
            return redirect('punto_venta_laboratorio')

    return redirect('punto_venta_laboratorio')
#######################################
@login_required
@user_passes_test(es_laboratorio)
def ticket_venta_ambulatoria(request, venta_id):
    """Mostrar ticket térmico para venta ambulatoria CON PRECIOS"""
    try:
        venta = VentaAmbulatoria.objects.get(id=venta_id)
        ordenes_examen = OrdenExamen.objects.filter(venta_ambulatoria=venta)
        
        # NUEVO: Crear lista con exámenes y sus precios
        examenes_con_precio = []
        total_verificado = 0
        
        for orden in ordenes_examen:
            # Buscar el precio del examen en el catálogo
            try:
                examen_catalogo = CatalogoExamen.objects.get(
                    nombre=orden.examen_especifico,
                    tipo='LABORATORIO',
                    activo=True
                )
                precio = examen_catalogo.precio
            except CatalogoExamen.DoesNotExist:
                # Si no encuentra en catálogo, usar monto_pagado o precio por defecto
                precio = orden.monto_pagado if hasattr(orden, 'monto_pagado') else Decimal('50.00')
            
            examenes_con_precio.append({
                'nombre': orden.examen_especifico,
                'precio_unitario': precio,
                'cantidad': 1,  # Cada orden es un examen
                'subtotal': precio
            })
            total_verificado += precio
        
        # Agrupar exámenes iguales
        examenes_agrupados = {}
        for item in examenes_con_precio:
            nombre = item['nombre']
            if nombre in examenes_agrupados:
                examenes_agrupados[nombre]['cantidad'] += 1
                examenes_agrupados[nombre]['subtotal'] += item['precio_unitario']
            else:
                examenes_agrupados[nombre] = {
                    'precio_unitario': item['precio_unitario'],
                    'cantidad': 1,
                    'subtotal': item['precio_unitario']
                }
        
        context = {
            'venta': venta,
            'fecha': venta.fecha_creacion,
            'usuario': request.user,
            'examenes_agrupados': examenes_agrupados,  # Ahora con precios
            'total_examenes': len(ordenes_examen),
            'total_verificado': total_verificado,
        }
        
    except VentaAmbulatoria.DoesNotExist:
        # Datos de ejemplo para desarrollo
        context = {
            'venta': {
                'id': venta_id,
                'paciente_nombre': 'PACIENTE EXTERNO',
                'paciente_dni': '87654321',
                'total': '185.50',
                'metodo_pago': 'EFECTIVO',
            },
            'fecha': timezone.now(),
            'usuario': request.user,
            'examenes_agrupados': {
                'HEMOGRAMA COMPLETO': {
                    'precio_unitario': Decimal('85.50'),
                    'cantidad': 1,
                    'subtotal': Decimal('85.50')
                },
                'GLUCOSA EN AYUNAS': {
                    'precio_unitario': Decimal('50.00'),
                    'cantidad': 2,
                    'subtotal': Decimal('100.00')
                },
            },
            'total_examenes': 3,
            'total_verificado': Decimal('185.50'),
        }
    
    return render(request, 'consultas/laboratorio/ticket_venta.html', context)

# ==============================================
# VISTAS PARA CONSULTAS (MANTENIDAS)
# ==============================================

def paciente_tiene_consulta_hoy(paciente, tarifa, doctor=None):
    """
    Verifica si un paciente ya tiene una consulta registrada hoy
    para el mismo tipo de consulta y especialidad.
    """
    hoy = now().date()

    consultas_hoy = Consulta.objects.filter(
        paciente=paciente,
        fecha__date=hoy,
        estado=Consulta.EstadoConsulta.REGISTRADA
    )

    if not consultas_hoy.exists():
        return False

    for consulta_existente in consultas_hoy:
        if (tarifa.tipo_consulta == 'GENERAL' and
            consulta_existente.tarifa.tipo_consulta == 'GENERAL'):
            return True

        if (tarifa.tipo_consulta == 'ECOGRAFIA' and
            consulta_existente.tarifa.tipo_consulta == 'ECOGRAFIA'):
            return True

        if (tarifa.tipo_consulta == 'ESPECIALIDAD' and
            consulta_existente.tarifa.tipo_consulta == 'ESPECIALIDAD' and
            tarifa.especialidad == consulta_existente.tarifa.especialidad):
            return True

        if doctor and consulta_existente.doctor == doctor:
            return True

    return False

def crear_consulta(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            tarifa = form.cleaned_data['tarifa']
            doctor = form.cleaned_data.get('doctor')
            hoy = now().date()

            existe = paciente_tiene_consulta_hoy(paciente, tarifa, doctor)
            if existe:
                if tarifa.tipo_consulta == 'GENERAL':
                    mensaje_error = 'El paciente ya tiene una consulta GENERAL registrada para hoy.'
                elif tarifa.tipo_consulta == 'ECOGRAFIA':
                    mensaje_error = 'El paciente ya tiene una ECOGRAFÍA registrada para hoy.'
                elif tarifa.tipo_consulta == 'ESPECIALIDAD':
                    mensaje_error = f'El paciente ya tiene una consulta de {tarifa.get_especialidad_display()} registrada para hoy.'
                else:
                    mensaje_error = 'El paciente ya tiene una consulta registrada para hoy.'

                return render(request, 'consultas/crear_consulta.html', {
                    'paciente': paciente,
                    'form': form,
                    'error': mensaje_error
                })

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
                        'error': f'El paciente ya tiene una consulta registrada hoy con el Dr. {doctor.nombres} {doctor.apellidos}.'
                    })

            consulta = form.save(commit=False)
            consulta.paciente = paciente
            consulta.save()

            orden = OrdenPago.objects.create(consulta=consulta)
            return redirect('detalle_orden_pago', orden.id)

    else:
        form = ConsultaForm()

    return render(request, 'consultas/crear_consulta.html', {
        'paciente': paciente,
        'form': form
    })

##################################################
# En views.py, añadir:
def buscar_ordenes_laboratorio(request):
    """Búsqueda global de órdenes por DNI en todos los estados"""
    dni_buscado = request.GET.get('dni', '').strip()
    estado_filtro = request.GET.get('estado', 'TODOS')

    if not dni_buscado:
        # Redirigir al dashboard si no hay búsqueda
        return redirect('lista_ordenes_pendientes')

    # Filtrar por DNI en TODOS los estados
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria',
        'tecnico_asignado'
    )

    # Aplicar filtro DNI
    dni_limpio = dni_buscado.replace(' ', '').replace('-', '').replace('.', '')

    if dni_limpio.isdigit() and len(dni_limpio) == 8:
        ordenes = ordenes.filter(
            Q(consulta__paciente__dni=dni_limpio) |
            Q(venta_ambulatoria__paciente_dni=dni_limpio)
        )
    else:
        ordenes = ordenes.filter(
            Q(consulta__paciente__dni__icontains=dni_buscado) |
            Q(venta_ambulatoria__paciente_dni__icontains=dni_buscado)
        )

    # Filtrar por estado si se especifica
    if estado_filtro != 'TODOS':
        ordenes = ordenes.filter(estado=estado_filtro)

    # Ordenar por fecha
    ordenes = ordenes.order_by('-fecha_solicitud')

    # Contar por estado
    contadores = {
        'SOLICITADO': ordenes.filter(estado='SOLICITADO').count(),
        'EN_PROCESO': ordenes.filter(estado='EN_PROCESO').count(),
        'COMPLETADO': ordenes.filter(estado='COMPLETADO').count(),
        'ENTREGADO': ordenes.filter(estado='ENTREGADO').count(),
        'TODOS': ordenes.count(),
    }

    context = {
        'ordenes': ordenes,
        'dni_buscado': dni_buscado,
        'estado_filtro': estado_filtro,
        'contadores': contadores,
        'titulo': f'Búsqueda: {dni_buscado}',
    }

    return render(request, 'consultas/laboratorio/busqueda_global.html', context)


#############################
def buscar_ordenes_simple(request):
    """Búsqueda simple por DNI"""
    dni = request.GET.get('dni', '').strip()

    if not dni:
        return redirect('lista_ordenes_pendientes')

    # Buscar simple
    ordenes = OrdenExamen.objects.filter(
        Q(consulta__paciente__dni__icontains=dni) |
        Q(venta_ambulatoria__paciente_dni__icontains=dni),
        tipo_examen='LABORATORIO'
    ).order_by('-fecha_solicitud')

    context = {
        'ordenes': ordenes,
        'dni_buscado': dni,
        'titulo': f'Búsqueda: {dni}',
    }

    return render(request, 'consultas/laboratorio/busqueda_simple.html', context)


########################
@login_required
@user_passes_test(es_laboratorio)
def buscar_ordenes_global(request):
    """Búsqueda global de órdenes por DNI"""
    dni_buscado = request.GET.get('dni', '').strip()

    if not dni_buscado:
        # Redirigir a pendientes si no hay búsqueda
        return redirect('lista_ordenes_pendientes')

    # Buscar en TODOS los estados
    ordenes = OrdenExamen.objects.filter(
        tipo_examen='LABORATORIO'
    ).select_related(
        'consulta__paciente',
        'venta_ambulatoria'
    )

    # Filtrar por DNI
    if dni_buscado:
        ordenes = ordenes.filter(
            Q(consulta__paciente__dni__icontains=dni_buscado) |
            Q(venta_ambulatoria__paciente_dni__icontains=dni_buscado)
        )

    # Ordenar por fecha más reciente
    ordenes = ordenes.order_by('-fecha_solicitud')

    # Contar por estado
    contadores = {
        'pendientes': ordenes.filter(estado='SOLICITADO').count(),
        'en_proceso': ordenes.filter(estado='EN_PROCESO').count(),
        'completados': ordenes.filter(estado='COMPLETADO').count(),
        'entregados': ordenes.filter(estado='ENTREGADO').count(),
        'total': ordenes.count(),
    }

    context = {
        'ordenes': ordenes,
        'dni_buscado': dni_buscado,
        'contadores': contadores,
        'titulo': f'Búsqueda: {dni_buscado}',
    }

    return render(request, 'consultas/laboratorio/busqueda_global.html', context)


########
@login_required
@require_POST  # IMPORTANTE: Solo por POST para seguridad
def cancelar_eliminar_orden(request, orden_id):
    """
    Elimina una orden pendiente del sistema
    Único caso: paciente no se presentó para los análisis
    """
    try:
        orden = get_object_or_404(OrdenExamen, id=orden_id)

        # SOLO se puede eliminar si cumple estas condiciones:
        if orden.estado != 'SOLICITADO':
            messages.error(request, f'No se puede eliminar la orden #{orden_id}. Solo órdenes pendientes.')
            return redirect('lista_ordenes_pendientes')

        if orden.tipo_examen != 'LABORATORIO':
            messages.error(request, f'La orden #{orden_id} no es de laboratorio.')
            return redirect('lista_ordenes_pendientes')

        if orden.tecnico_asignado:
            messages.error(request, f'No se puede eliminar la orden #{orden_id} porque ya está asignada.')
            return redirect('lista_ordenes_pendientes')

        # Guardar info para el mensaje (antes de eliminar)
        paciente_nombre = ""
        if orden.consulta:
            paciente_nombre = f"{orden.consulta.paciente.nombres} {orden.consulta.paciente.apellidos}"
        elif orden.venta_ambulatoria:
            paciente_nombre = orden.venta_ambulatoria.paciente_nombre

        # ELIMINAR la orden (no cancelar, ELIMINAR)
        orden.delete()

        messages.success(request,
            f'✅ Orden #{orden_id} eliminada correctamente. '
            f'Paciente: {paciente_nombre}'
        )

    except Exception as e:
        messages.error(request, f'❌ Error al eliminar orden: {str(e)}')

    return redirect('lista_ordenes_pendientes')



#################
@login_required
@user_passes_test(es_laboratorio)
@require_POST
def cobrar_ordenes_seleccionadas(request):
    """Versión simplificada y segura - CON VALIDACIÓN DE NO MEZCLA"""

    # ✅ VALIDACIÓN SIMPLE: Si tiene exámenes nuevos, NO agregar órdenes internas
    carrito = request.session.get('carrito_laboratorio', {})
    tiene_examenes_nuevos = any(not k.startswith('orden_interna_') for k in carrito.keys())

    if tiene_examenes_nuevos:
        messages.error(request, '❌ No puedes agregar órdenes internas porque ya tienes exámenes nuevos en el carrito.')
        return redirect('lista_ordenes_pendientes')

    # RESTO DE TU CÓDIGO ORIGINAL (con corrección de precios)
    ordenes_ids = [int(id) for id in request.POST.getlist('ordenes_ids') if id.isdigit()]

    if not ordenes_ids:
        messages.error(request, '❌ No se seleccionaron órdenes')
        return redirect('lista_ordenes_pendientes')

    # Inicializar carrito
    request.session.setdefault('carrito_laboratorio', {})
    carrito = request.session['carrito_laboratorio']

    # Contar items antes
    items_iniciales = len(carrito)

    for orden_id in ordenes_ids:
        try:
            orden = OrdenExamen.objects.get(id=orden_id)

            # Solo órdenes internas no pagadas
            if orden.consulta and not orden.pagado:
                item_id = f"orden_interna_{orden.id}"

                if item_id not in carrito:
                    # ✅ CORRECCIÓN: BUSCAR PRECIO REAL EN CATÁLOGO
                    precio_final = "0.00"
                    
                    # BUSCAR EN CATÁLOGO SEGÚN TIPO DE EXAMEN
                    if orden.tipo_examen == 'LABORATORIO':
                        # Buscar en CatalogoExamen
                        try:
                            examen_catalogo = CatalogoExamen.objects.get(
                                nombre=orden.examen_especifico,
                                tipo='LABORATORIO',
                                activo=True
                            )
                            precio_final = str(examen_catalogo.precio)
                        except CatalogoExamen.DoesNotExist:
                            # Si no encuentra, usar 50 como fallback (igual que antes)
                            precio_final = "50.00"
                            
                    elif orden.tipo_examen == 'ECOGRAFIA':
                        # Buscar en CatalogoEcografia
                        try:
                            eco_catalogo = CatalogoEcografia.objects.get(
                                nombre=orden.examen_especifico,
                                activo=True
                            )
                            precio_final = str(eco_catalogo.precio)
                        except CatalogoEcografia.DoesNotExist:
                            precio_final = "50.00"
                    else:
                        # Para otros tipos, usar 50
                        precio_final = "50.00"

                    carrito[item_id] = {
                        'id': item_id,
                        'orden_id': orden.id,
                        'nombre': f"Orden #{orden.id} - {orden.examen_especifico}",
                        'tipo': 'INTERNO_POR_COBRAR',
                        'precio': precio_final,  # ✅ AHORA PRECIO REAL
                        'cantidad': 1,
                        'paciente': orden.get_paciente_nombre(),
                        'es_interno': True,
                        # ✅ NUEVO: Guardar info del catálogo para referencia
                        'tipo_examen': orden.tipo_examen,
                        'examen_especifico': orden.examen_especifico,
                    }

        except (OrdenExamen.DoesNotExist, ValueError):
            continue

    request.session.modified = True

    items_finales = len(carrito)
    items_agregados = items_finales - items_iniciales

    if items_agregados > 0:
        messages.success(request, f'✅ {items_agregados} orden(es) agregada(s) al carrito')
        return redirect('punto_venta_laboratorio')
    else:
        messages.error(request, '❌ No se agregaron nuevas órdenes al carrito')
        return redirect('lista_ordenes_pendientes')
##############################
@login_required
@user_passes_test(es_laboratorio)
def ticket_cobro_interno(request, venta_id):
    """Ticket para cobro de órdenes internas - VERSIÓN CORREGIDA CON DESCUENTO"""
    venta = get_object_or_404(VentaAmbulatoria, id=venta_id)

    # Obtener órdenes cobradas de la sesión
    datos_cobro = request.session.get('ultimas_ordenes_cobradas', {})
    ordenes_detalles = datos_cobro.get('detalles', [])

    # DEBUG: Ver qué datos hay en la sesión
    print(f"[DEBUG TICKET] Datos en sesión: {datos_cobro}")
    print(f"[DEBUG TICKET] Descuento en sesión: {datos_cobro.get('descuento', 'NO HAY')}")
    print(f"[DEBUG TICKET] Total en sesión: {datos_cobro.get('total', 'NO HAY')}")

    # Convertir los precios de float (de JSON) a Decimal para el template
    ordenes_con_precio_correcto = []
    total_sin_descuento = Decimal('0.00')
    total_con_descuento = Decimal('0.00')

    if ordenes_detalles:
        for oc in ordenes_detalles:
            try:
                # Precio original (desde datos de sesión)
                precio_original = Decimal(str(oc.get('precio_original', 50.00)))
            except:
                precio_original = Decimal('50.00')

            try:
                # Precio con descuento (desde datos de sesión)
                precio_final = Decimal(str(oc.get('precio_final', oc.get('precio_con_descuento', oc.get('precio', precio_original)))))
            except:
                precio_final = precio_original

            descuento_individual = precio_original - precio_final

            ordenes_con_precio_correcto.append({
                'id': oc.get('id'),
                'examen': oc.get('examen', 'Examen no especificado'),
                'precio_original': precio_original,
                'precio_final': precio_final,
                'descuento_individual': descuento_individual,
                'paciente': oc.get('paciente', 'Paciente no identificado'),
                'dni': oc.get('dni', '')
            })

            total_sin_descuento += precio_original
            total_con_descuento += precio_final

    # Si no hay datos en sesión, buscar en BD (fallback)
    if not ordenes_con_precio_correcto:
        # Buscar órdenes pagadas recientemente (últimos 5 minutos)
        desde = timezone.now() - timedelta(minutes=5)

        ordenes_db = OrdenExamen.objects.filter(
            pagado=True,
            fecha_pago__gte=desde,
            consulta__isnull=False  # Solo internas
        ).select_related('consulta__paciente').order_by('-fecha_pago')

        for orden in ordenes_db:
            # Precio original (asumir 50.00)
            precio_original = Decimal('50.00')

            # Precio final (con descuento si aplica)
            precio_final = orden.monto_pagado if hasattr(orden, 'monto_pagado') and orden.monto_pagado else precio_original

            descuento_individual = precio_original - precio_final

            ordenes_con_precio_correcto.append({
                'id': orden.id,
                'examen': orden.examen_especifico,
                'precio_original': precio_original,
                'precio_final': precio_final,
                'descuento_individual': descuento_individual,
                'paciente': orden.get_paciente_nombre(),
                'dni': orden.get_paciente_dni()
            })

            total_sin_descuento += precio_original
            total_con_descuento += precio_final

    # Obtener descuento de la sesión (¡USAR EL DE LA SESIÓN!)
    try:
        descuento_total = Decimal(str(datos_cobro.get('descuento', 0)))
    except:
        descuento_total = Decimal('0.00')

    # Si el descuento de la sesión es 0 pero venta tiene descuento, usar el de venta
    if descuento_total == 0 and venta.descuento_aplicado > 0:
        descuento_total = Decimal(str(venta.descuento_aplicado))
        print(f"[DEBUG TICKET] Usando descuento de venta: {descuento_total}")

    # Si todavía es 0, calcularlo a partir de los precios
    if descuento_total == 0:
        descuento_total = total_sin_descuento - total_con_descuento
        print(f"[DEBUG TICKET] Calculando descuento: {descuento_total}")

    # Calcular total final (usar el de la sesión si existe)
    try:
        total_final_sesion = Decimal(str(datos_cobro.get('total_con_descuento', total_con_descuento)))
        total_final = total_final_sesion
    except:
        total_final = total_con_descuento

    # DEBUG: Imprimir valores para diagnóstico
    print(f"[DEBUG TICKET] total_sin_descuento: {total_sin_descuento}")
    print(f"[DEBUG TICKET] total_con_descuento: {total_con_descuento}")
    print(f"[DEBUG TICKET] descuento_total: {descuento_total}")
    print(f"[DEBUG TICKET] total_final: {total_final}")
    print(f"[DEBUG TICKET] Descuento de venta: {venta.descuento_aplicado}")

    # Preparar contexto
    context = {
        'venta': venta,
        'ordenes': ordenes_con_precio_correcto,
        'total_sin_descuento': total_sin_descuento,
        'descuento_total': descuento_total,
        'total_final': total_final,
        'metodo_pago': datos_cobro.get('metodo_pago', 'EFECTIVO'),
        'fecha': timezone.now(),
        'usuario': request.user,
        'es_cobro_interno': True,
        'cantidad_ordenes': len(ordenes_con_precio_correcto),
    }

    # Limpiar datos de sesión después de usarlos
    if 'ultimas_ordenes_cobradas' in request.session:
        del request.session['ultimas_ordenes_cobradas']
        request.session.modified = True

    return render(request, 'consultas/laboratorio/ticket_cobro_interno.html', context)

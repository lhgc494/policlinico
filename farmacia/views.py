# farmacia/views.py - VERSIÓN COMPLETA CORREGIDA
from datetime import date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json
from django.db import transaction
from config.decorators import grupo_requerido
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import ComboTopico, Medicamento
from config.decorators import grupo_requerido
from consultas.models import TopicoCatalogo
# ¡IMPORTANTE! SOLO MODELOS QUE EXISTEN en el NUEVO models.py
from .models import (
    Medicamento, 
    Categoria, 
    Presentacion, 
    Proveedor, 
    MovimientoInventario,
    Venta,           # ¡MODELO CORRECTO!
    DetalleVenta,    # ¡MODELO CORRECTO!
    Compra,          
    DetalleCompra
)
from .forms import MedicamentoForm, ProveedorForm, CategoriaForm


# ==============================================
# DECORADOR PARA VERIFICAR GRUPO FARMACIA
# ==============================================

@login_required
def es_farmacia(user):
    """Verifica si el usuario pertenece al grupo farmacia"""
    return user.groups.filter(name='farmacia').exists()

# ==============================================
# VISTAS PRINCIPALES DE INVENTARIO
# ==============================================
###lista medicamento ##########
@login_required
@never_cache
@grupo_requerido('administrador')
def lista_medicamentos(request):
    """Lista todos los medicamentos con filtros"""
    # Obtener parámetros de filtro
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    activo = request.GET.get('activo', 'si')  # 'si', 'no', 'todos'

    # Query base
    medicamentos_qs = Medicamento.objects.all()

    # Aplicar filtros
    if query:
        medicamentos_qs = medicamentos_qs.filter(
            Q(codigo__icontains=query) |
            Q(nombre_comercial__icontains=query) |
            Q(principio_activo__icontains=query) |
            Q(lote__icontains=query)
        )

    if categoria_id:
        medicamentos_qs = medicamentos_qs.filter(categoria_id=categoria_id)

    if activo == 'si':
        medicamentos_qs = medicamentos_qs.filter(activo=True)
    elif activo == 'no':
        medicamentos_qs = medicamentos_qs.filter(activo=False)
    # Si es 'todos', no filtramos

    # Ordenar
    medicamentos_qs = medicamentos_qs.order_by('nombre_comercial')

    # Paginación
    paginator = Paginator(medicamentos_qs, 15)
    page_number = request.GET.get('page')
    medicamentos = paginator.get_page(page_number)

    # Obtener categorías para el filtro
    categorias = Categoria.objects.filter(activa=True)

    # Estadísticas - ¡CORREGIDO!
    total_medicamentos = Medicamento.objects.count()
    activos_count = Medicamento.objects.filter(activo=True).count()
    inactivos_count = Medicamento.objects.filter(activo=False).count()
    
    # Calcular contadores de propiedades (EN MEMORIA)
    medicamentos_activos = Medicamento.objects.filter(activo=True)
    bajo_stock_count = sum(1 for m in medicamentos_activos if m.bajo_stock)
    proximos_vencer_count = sum(1 for m in medicamentos_activos if m.proximo_vencer)

    context = {
        'medicamentos': medicamentos,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id,
        'activo': activo,
        'titulo': 'Inventario de Medicamentos',

        # Estadísticas
        'total_medicamentos': total_medicamentos,
        'activos_count': activos_count,
        'inactivos_count': inactivos_count,
        'bajo_stock': bajo_stock_count,           # ¡NOMBRE CORREGIDO!
        'proximos_vencer': proximos_vencer_count, # ¡NOMBRE CORREGIDO!
    }

    return render(request, 'farmacia/lista_medicamentos.html', context)

###########################
@login_required
@never_cache
def detalle_medicamento(request, id):
    """Muestra el detalle de un medicamento"""
    medicamento = get_object_or_404(Medicamento, id=id)

    # Obtener historial de movimientos
    movimientos = MovimientoInventario.objects.filter(
        medicamento=medicamento
    ).order_by('-fecha')[:10]

    context = {
        'medicamento': medicamento,
        'movimientos': movimientos,
        'titulo': f'Detalle: {medicamento.nombre_comercial}'
    }

    return render(request, 'farmacia/detalle_medicamento.html', context)
###############
@login_required
@never_cache
def crear_medicamento(request):
    """Paso 2.1: Crear medicamento con stock inicial"""
    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            try:
                # Guardar el medicamento
                medicamento = form.save(commit=False)
                medicamento.save()  # ✅ Esto guarda el stock_actual del form

                # ✅ PASO 2.2: Registrar movimiento de ENTRADA por stock inicial
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo='ENTRADA',  # Es una entrada porque aumenta stock
                    cantidad=medicamento.stock_actual,
                    usuario=request.user,
                    referencia='Stock inicial al crear medicamento',
                    precio_unitario=medicamento.precio_compra
                )

                messages.success(request, f'✅ Medicamento creado: {medicamento.nombre_comercial}')
                return redirect('farmacia:lista_medicamentos')
                
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
        else:
            messages.error(request, '❌ Corrige los errores del formulario')
    else:
        form = MedicamentoForm()

    return render(request, 'farmacia/crear_medicamento.html', {'form': form, 'titulo': 'Nuevo Medicamento'})


####################
@login_required
@never_cache
def editar_medicamento(request, id):
    """Edita un medicamento existente - VERSIÓN FINAL CORREGIDA"""
    medicamento = get_object_or_404(Medicamento, id=id)
    
    # Guardar stock original ANTES de procesar el formulario
    stock_original = medicamento.stock_actual

    if request.method == 'POST':
        form = MedicamentoForm(request.POST, instance=medicamento)
        if form.is_valid():
            try:
                # Guardar cambios (el formulario NO debe incluir stock_actual)
                medicamento = form.save(commit=False)
                
                # 🔴 IMPORTANTE: RESTAURAR el stock original
                # Por si acaso el formulario intentó modificarlo
                medicamento.stock_actual = stock_original
                
                # Guardar solo los cambios del formulario
                medicamento.save()
                
                # ⚠️ NOTA: Ya NO comparamos stock porque no cambió
                # El stock SOLO se modifica mediante movimientos
                
                messages.success(
                    request,
                    f'✅ Medicamento actualizado: {medicamento.nombre_comercial}'
                )
                    
                return redirect('farmacia:detalle_medicamento', id=medicamento.id)

            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error al actualizar medicamento: {str(e)}'
                )
        else:
            messages.error(
                request,
                '❌ Por favor corrige los errores en el formulario'
            )
    else:
        form = MedicamentoForm(instance=medicamento)

    context = {
        'form': form,
        'medicamento': medicamento,
        'stock_original': stock_original,  # Pasar al template
        'titulo': f'Editar: {medicamento.nombre_comercial}'
    }

    return render(request, 'farmacia/editar_medicamento.html', context)
######################
@login_required
@never_cache
def eliminar_medicamento(request, id):
    """Elimina (desactiva) un medicamento - VERSIÓN CORREGIDA"""
    medicamento = get_object_or_404(Medicamento, id=id)

    if request.method == 'POST':
        try:
            # Verificar si tiene stock antes de desactivar
            if medicamento.stock_actual > 0:
                messages.warning(
                    request,
                    f'⚠️ El medicamento tiene {medicamento.stock_actual} unidades en stock. '
                    f'Considera hacer un ajuste de inventario primero.'
                )
                # Opcional: preguntar si quiere continuar
            
            # Marcar como inactivo en lugar de eliminar
            medicamento.activo = False
            medicamento.save()
            
            # ✅ OPCIONAL: Registrar movimiento de PERDIDA si se desactiva con stock
            if medicamento.stock_actual > 0:
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo='PERDIDA',
                    cantidad=medicamento.stock_actual,
                    usuario=request.user,
                    referencia=f'Medicamento desactivado - Stock dado de baja',
                    precio_unitario=medicamento.precio_compra
                )
                messages.warning(
                    request,
                    f'⚠️ Se registró una pérdida de {medicamento.stock_actual} unidades'
                )

            messages.success(
                request,
                f'✅ Medicamento desactivado: {medicamento.nombre_comercial}'
            )
            return redirect('farmacia:lista_medicamentos')

        except Exception as e:
            messages.error(
                request,
                f'❌ Error al desactivar medicamento: {str(e)}'
            )
            return redirect('farmacia:lista_medicamentos')

    context = {
        'medicamento': medicamento,
        'titulo': f'Desactivar: {medicamento.nombre_comercial}',
        'advertencia_stock': medicamento.stock_actual > 0
    }

    return render(request, 'farmacia/confirmar_eliminar.html', context)
# ==============================================
# VISTAS DE GESTIÓN DE INVENTARIO
# ==============================================
@login_required
@never_cache
def ajustar_inventario(request, id):
    """Ajusta el stock de un medicamento - AJUSTE_POSITIVO o AJUSTE_NEGATIVO"""
    medicamento = get_object_or_404(Medicamento, id=id)

    if request.method == 'POST':
        tipo = request.POST.get('tipo')  # 'entrada' o 'salida'
        cantidad = int(request.POST.get('cantidad', 0))
        motivo = request.POST.get('motivo', '')

        if cantidad <= 0:
            messages.error(request, '❌ La cantidad debe ser mayor a 0')
            return redirect('farmacia:detalle_medicamento', id=id)

        try:
            from django.db import transaction
            
            with transaction.atomic():
                if tipo == 'entrada':
                    movimiento_tipo = 'AJUSTE_POSITIVO'  # ✅ NUEVO TIPO
                    signo = '+'
                    mensaje = f'✅ Ajuste +: +{cantidad} unidades'
                else:
                    if cantidad > medicamento.stock_actual:
                        messages.error(
                            request,
                            f'❌ Stock insuficiente. Disponible: {medicamento.stock_actual}'
                        )
                        return redirect('farmacia:detalle_medicamento', id=id)
                    
                    movimiento_tipo = 'AJUSTE_NEGATIVO'  # ✅ NUEVO TIPO
                    signo = '-'
                    mensaje = f'✅ Ajuste -: -{cantidad} unidades'
                
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo=movimiento_tipo,
                    cantidad=cantidad,
                    usuario=request.user,
                    referencia=f'Ajuste manual: {motivo} ({signo}{cantidad})',
                    precio_unitario=medicamento.precio_compra
                )
                
                messages.success(request, mensaje)

        except Exception as e:
            messages.error(request, f'❌ Error al ajustar inventario: {str(e)}')

        return redirect('farmacia:detalle_medicamento', id=id)

    context = {
        'medicamento': medicamento,
        'titulo': f'Ajustar Stock: {medicamento.nombre_comercial}'
    }
    return render(request, 'farmacia/ajustar_inventario.html', context)


@login_required
@never_cache
def historial_movimientos(request):
    """Muestra el historial de movimientos de inventario"""
    # Filtros
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    tipo = request.GET.get('tipo', '')
    medicamento_id = request.GET.get('medicamento', '')

    # Query base
    movimientos_qs = MovimientoInventario.objects.select_related(
        'medicamento', 'usuario'
    ).order_by('-fecha')

    # Aplicar filtros
    if fecha_desde:
        movimientos_qs = movimientos_qs.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        movimientos_qs = movimientos_qs.filter(fecha__lte=fecha_hasta)

    if tipo:
        movimientos_qs = movimientos_qs.filter(tipo=tipo)

    if medicamento_id:
        movimientos_qs = movimientos_qs.filter(medicamento_id=medicamento_id)

    # Paginación
    paginator = Paginator(movimientos_qs, 20)
    page_number = request.GET.get('page')
    movimientos = paginator.get_page(page_number)

    # Datos para filtros
    medicamentos = Medicamento.objects.filter(activo=True).order_by('nombre_comercial')

    context = {
        'movimientos': movimientos,
        'medicamentos': medicamentos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'tipo': tipo,
        'medicamento_id': medicamento_id,
        'titulo': 'Historial de Movimientos'
    }

    return render(request, 'farmacia/historial_movimientos.html', context)

# ==============================================
# VISTAS DE REPORTES
# ==============================================
####### reporte stock bajo #########
@login_required
@never_cache
def reporte_stock_bajo(request):
    """Muestra medicamentos con stock bajo el mínimo"""
    
    # Obtener todos los medicamentos activos
    medicamentos_activos = Medicamento.objects.filter(activo=True)
    
    # Filtrar usando propiedades (en memoria) - ¡CORREGIDO!
    medicamentos_bajo_stock = [
        m for m in medicamentos_activos 
        if m.bajo_stock  # Esta es una propiedad, no campo de BD
    ]
    
    # Ordenar por stock actual
    medicamentos_bajo_stock.sort(key=lambda x: x.stock_actual)

    context = {
        'medicamentos': medicamentos_bajo_stock,
        'titulo': 'Medicamentos con Stock Bajo',
        'total': len(medicamentos_bajo_stock)
    }

    return render(request, 'farmacia/reportes/stock_bajo.html', context)

####proximo a vencer#################
@login_required
@never_cache
def reporte_proximos_vencer(request):
    """Muestra medicamentos próximos a vencer (hasta 4 meses)"""
    from datetime import date, timedelta
    
    hoy = date.today()
    limite_4_meses = hoy + timedelta(days=120)  # 4 meses ≈ 120 días
    limite_1_mes = hoy + timedelta(days=30)
    limite_2_meses = hoy + timedelta(days=60)
    
    # Obtener todos los medicamentos activos con fecha de vencimiento
    medicamentos_con_fecha = Medicamento.objects.filter(
        activo=True,
        fecha_vencimiento__isnull=False
    )
    
    # Clasificar por urgencia
    vencidos = []
    urgencia_alta = []    # < 30 días
    urgencia_media = []    # 30-60 días
    urgencia_baja = []     # 60-120 días
    
    for m in medicamentos_con_fecha:
        if m.fecha_vencimiento < hoy:
            vencidos.append(m)
        elif m.fecha_vencimiento <= limite_1_mes:
            urgencia_alta.append(m)
        elif m.fecha_vencimiento <= limite_2_meses:
            urgencia_media.append(m)
        elif m.fecha_vencimiento <= limite_4_meses:
            urgencia_baja.append(m)
    
    # Ordenar cada lista por fecha
    vencidos.sort(key=lambda x: x.fecha_vencimiento)
    urgencia_alta.sort(key=lambda x: x.fecha_vencimiento)
    urgencia_media.sort(key=lambda x: x.fecha_vencimiento)
    urgencia_baja.sort(key=lambda x: x.fecha_vencimiento)
    
    # Total de próximos a vencer (excluyendo vencidos)
    total_proximos = len(urgencia_alta) + len(urgencia_media) + len(urgencia_baja)
    
    context = {
        'vencidos': vencidos,
        'urgencia_alta': urgencia_alta,
        'urgencia_media': urgencia_media,
        'urgencia_baja': urgencia_baja,
        'total_vencidos': len(vencidos),
        'total_proximos': total_proximos,
        'limite_4_meses': limite_4_meses.strftime('%d/%m/%Y'),
        'hoy': hoy.strftime('%d/%m/%Y'),
        'titulo': 'Medicamentos Próximos a Vencer (4 meses)'
    }
    
    return render(request, 'farmacia/reportes/proximos_vencer.html', context)

##############
@login_required
@never_cache
def reporte_valor_inventario(request):
    """Muestra el valor total del inventario por categoría"""
    # Valor total por categoría
    categorias_valor = Medicamento.objects.filter(activo=True).values(
        'categoria__nombre'
    ).annotate(
        total_valor=Sum('valor_inventario'),
        total_unidades=Sum('stock_actual')
    ).order_by('-total_valor')

    # Valor total general
    valor_total = Medicamento.objects.filter(activo=True).aggregate(
        total=Sum('valor_inventario')
    )['total'] or 0

    # Valor de venta total
    try:
        valor_venta_total = sum(
            m.valor_venta_inventario for m in
            Medicamento.objects.filter(activo=True)
        )
    except:
        valor_venta_total = 0

    # Datos para gráfico
    datos_grafico = {
        'labels': [item['categoria__nombre'] or 'Sin categoría'
                  for item in categorias_valor],
        'data': [float(item['total_valor'] or 0)
                for item in categorias_valor]
    }

    context = {
        'categorias_valor': categorias_valor,
        'valor_total': valor_total,
        'valor_venta_total': valor_venta_total,
        'datos_grafico': json.dumps(datos_grafico),
        'titulo': 'Valor del Inventario'
    }

    return render(request, 'farmacia/reportes/valor_inventario.html', context)

# ==============================================
# VISTAS DE GESTIÓN (PROVEEDORES, CATEGORÍAS)
# ==============================================

@login_required
@never_cache
def detalle_proveedor(request, id):
    """Muestra el detalle completo de un proveedor"""
    proveedor = get_object_or_404(Proveedor, id=id)

    # Obtener medicamentos suministrados por este proveedor
    medicamentos = proveedor.medicamentos.filter(activo=True).order_by('nombre_comercial')

    # Estadísticas
    total_medicamentos = medicamentos.count()
    total_valor_inventario = sum(m.valor_inventario for m in medicamentos)

    context = {
        'proveedor': proveedor,
        'medicamentos': medicamentos,
        'total_medicamentos': total_medicamentos,
        'total_valor_inventario': total_valor_inventario,
        'titulo': f'Proveedor: {proveedor.nombre}'
    }

    return render(request, 'farmacia/proveedores/detalle.html', context)

@login_required
@never_cache
@grupo_requerido('administrador')
def lista_proveedores(request):
    """Lista todos los proveedores"""
    proveedores = Proveedor.objects.all().order_by('nombre')

    context = {
        'proveedores': proveedores,
        'titulo': 'Proveedores'
    }
    return render(request, 'farmacia/proveedores/lista.html', context)

@login_required
@never_cache
def crear_proveedor(request):
    """Crea un nuevo proveedor"""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Proveedor creado exitosamente')
            return redirect('farmacia:lista_proveedores')
    else:
        form = ProveedorForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Proveedor'
    }
    return render(request, 'farmacia/proveedores/crear.html', context)

@login_required
@never_cache
def editar_proveedor(request, id):
    """Edita un proveedor existente"""
    proveedor = get_object_or_404(Proveedor, id=id)

    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Proveedor actualizado exitosamente')
            return redirect('farmacia:lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)

    context = {
        'form': form,
        'proveedor': proveedor,
        'titulo': f'Editar: {proveedor.nombre}'
    }
    return render(request, 'farmacia/proveedores/editar.html', context)

@login_required
@never_cache
def eliminar_proveedor(request, id):
    """Elimina un proveedor"""
    proveedor = get_object_or_404(Proveedor, id=id)

    if request.method == 'POST':
        # Verificar si tiene medicamentos asociados
        if proveedor.medicamentos.exists():
            messages.error(request, '❌ No se puede eliminar. Hay medicamentos asociados a este proveedor.')
        else:
            proveedor.delete()
            messages.success(request, '✅ Proveedor eliminado exitosamente')
        return redirect('farmacia:lista_proveedores')

    context = {
        'proveedor': proveedor,
        'titulo': f'Eliminar: {proveedor.nombre}'
    }
    return render(request, 'farmacia/proveedores/eliminar.html', context)

# ==============================================
# VISTAS DE RECETAS Y CONSULTAS
# ==============================================

@login_required
@never_cache
@grupo_requerido('farmacia', 'administrador')
def recetas_pendientes(request):
    """Lista consultas con recetas pendientes"""
    from consultas.models import Consulta, Receta
    from doctores.models import Doctor
    from datetime import timedelta

    # Obtener parámetros de filtro
    dni = request.GET.get('dni', '')
    doctor_id = request.GET.get('doctor', '')
    fecha_filtro = request.GET.get('fecha', '')
    estado_filtro = request.GET.get('estado', 'pendientes')  # pendientes, todas

    # Obtener consultas que tienen recetas
    consultas = Consulta.objects.filter(
        recetas__isnull=False
    ).distinct().select_related(
        'paciente', 'doctor'
    ).prefetch_related('recetas')

    # Aplicar filtros
    if dni:
        consultas = consultas.filter(paciente__dni__icontains=dni)

    if doctor_id:
        consultas = consultas.filter(doctor_id=doctor_id)

    if fecha_filtro:
        hoy = timezone.now().date()
        if fecha_filtro == 'hoy':
            consultas = consultas.filter(fecha__date=hoy)
        elif fecha_filtro == 'semana':
            semana_pasada = hoy - timedelta(days=7)
            consultas = consultas.filter(fecha__date__gte=semana_pasada)
        elif fecha_filtro == 'mes':
            mes_pasado = hoy - timedelta(days=30)
            consultas = consultas.filter(fecha__date__gte=mes_pasado)

    # Filtrar por estado de recetas
    if estado_filtro == 'pendientes':
        consultas = consultas.filter(
            recetas__estado__in=['PENDIENTE', 'PARCIAL']
        ).distinct()

    # Ordenar
    consultas = consultas.order_by('-fecha')

    # Obtener médicos para el filtro
    doctores = Doctor.objects.filter(activo=True).order_by('nombres')

    # Calcular total de recetas por consulta
    for consulta in consultas:
        consulta.total_recetas = consulta.recetas.count()
        consulta.pendientes = consulta.recetas.filter(
            estado__in=['PENDIENTE', 'PARCIAL']
        ).count()

    context = {
        'consultas': consultas,
        'doctores': doctores,
        'dni': dni,
        'doctor_id': doctor_id,
        'fecha_filtro': fecha_filtro,
        'estado_filtro': estado_filtro,
        'titulo': 'Recetas Pendientes por Consulta'
    }
    return render(request, 'farmacia/recetas_pendientes.html', context)

@login_required
@never_cache
def cancelar_recetas_consulta(request, consulta_id):
    """Cancela todas las recetas de una consulta"""
    from consultas.models import Consulta

    if request.method == 'POST':
        try:
            consulta = get_object_or_404(Consulta, id=consulta_id)
            recetas = consulta.recetas.all()

            # Contar recetas canceladas
            canceladas = 0
            for receta in recetas:
                if receta.estado in ['PENDIENTE', 'PARCIAL']:
                    receta.estado = 'CANCELADA'
                    receta.usuario_atencion = request.user
                    receta.fecha_atencion = timezone.now()
                    receta.observaciones_farmacia = 'Cancelado por farmacia - Paciente no compró'
                    receta.save()
                    canceladas += 1

            return JsonResponse({
                'success': True,
                'message': f'Se cancelaron {canceladas} receta(s)',
                'canceladas': canceladas
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al cancelar recetas: {str(e)}'
            }, status=500)

    # Si no es POST, devolver error
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido. Use POST.'
    }, status=405)

#####################
# farmacia/views.py - CORREGIDO CON STOCK COMO LÍMITE
# farmacia/views.py - CORREGIDO CON STOCK COMO LÍMITE Y FILTRO DE ATENDIDAS
@login_required
@grupo_requerido('farmacia', 'administrador')
@never_cache
def detalle_recetas_consulta(request, consulta_id):
    """Muestra detalle de recetas - STOCK como límite (solo pendientes)"""
    from consultas.models import Consulta
    
    consulta = get_object_or_404(Consulta, id=consulta_id)
    
    # 🔴 CORREGIDO: Excluir recetas atendidas
    recetas = consulta.recetas.exclude(estado='ATENDIDA').order_by('medicamento')
    
    total_general = Decimal('0')
    
    for receta in recetas:
        try:
            # 1. Buscar medicamento en inventario
            medicamento_qs = Medicamento.objects.filter(
                activo=True,
                nombre_comercial__icontains=receta.medicamento.split()[0]
            ).first()
            
            # Valores por defecto
            stock_disponible = 0
            precio_unitario = Decimal('0')
            maximo_hoy = 0
            cantidad_sugerida = 0
            tiene_stock = False
            
            if medicamento_qs:
                stock_disponible = medicamento_qs.stock_actual
                precio_unitario = medicamento_qs.precio_venta
                tiene_stock = stock_disponible > 0
                
                # 2. El MÁXIMO es el stock disponible
                maximo_hoy = stock_disponible
                
                # 3. Cantidad sugerida: todo el stock
                if stock_disponible > 0:
                    cantidad_sugerida = stock_disponible
                else:
                    cantidad_sugerida = 0
            else:
                # Medicamento no encontrado en inventario
                maximo_hoy = 0
                cantidad_sugerida = 0
            
            # 4. Calcular subtotal
            subtotal = cantidad_sugerida * precio_unitario
            
            # 5. Asignar valores a la receta
            receta.stock_disponible = stock_disponible
            receta.precio_unitario = precio_unitario
            receta.maximo_hoy = maximo_hoy
            receta.cantidad_sugerida = cantidad_sugerida
            receta.subtotal = subtotal
            receta.tiene_stock = tiene_stock
            
            # 6. Sumar al total general
            total_general += subtotal
            
        except Exception as e:
            print(f"Error con receta {receta.id}: {e}")
            receta.stock_disponible = 0
            receta.precio_unitario = Decimal('0')
            receta.maximo_hoy = 0
            receta.cantidad_sugerida = 0
            receta.subtotal = Decimal('0')
            receta.tiene_stock = False
    
    context = {
        'consulta': consulta,
        'recetas': recetas,
        'total_general': total_general
    }
    return render(request, 'farmacia/atencion_recetas.html', context)

# ==============================================
# VISTAS DE VENTA DIRECTA (ACTUALIZADAS)
# ==============================================

@login_required
@never_cache
@grupo_requerido('farmacia', 'administrador')
def venta_directa(request):
    """Venta directa con búsqueda AJAX - Vista principal"""
    context = {
        'titulo': 'Venta Directa',
    }
    return render(request, 'farmacia/venta_directa.html', context)
############ venta directa #############
@login_required
@grupo_requerido('farmacia', 'administrador')
def procesar_venta_directa(request):
    print(f"\n{'='*60}")
    print(f"🔍 PROCESAR VENTA - INICIO")
    print(f"{'='*60}")
    print(f"Usuario: {request.user.username}")
    print(f"Session ID: {request.session.session_key}")
    print(f"Método: {request.method}")
    print(f"POST: {dict(request.POST)}")
    
    # ============================================
    # VERIFICAR SI LA PETICIÓN ES AJAX
    # ============================================
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    print(f"📡 ¿Es AJAX? {is_ajax}")
    print(f"📡 Headers: {dict(request.headers)}")
    
    # PREVENIR DOBLE SUBMIT: Verificar si ya hay una venta en proceso
    if hasattr(request, 'venta_en_proceso'):
        print(f"⚠️ Venta ya en proceso - ignorando")
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': 'Ya hay una venta en proceso'})
        else:
            messages.error(request, 'Ya hay una venta en proceso')
            return redirect('farmacia:venta_directa')
    
    request.venta_en_proceso = True  # Marcar para evitar duplicados
    
    try:
        # ============================================
        # DEPURACIÓN: Ver el carrito completo de la sesión
        # ============================================
        carrito_raw = request.session.get('carrito_venta_directa', [])
        print(f"\n📋 CARRITO EN SESIÓN ({len(carrito_raw)} items):")
        for i, item in enumerate(carrito_raw):
            print(f"  Item {i}: {item}")
        
        if not carrito_raw:
            print(f"❌ Carrito vacío")
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': 'El carrito está vacío'})
            else:
                messages.error(request, 'El carrito está vacío')
                return redirect('farmacia:venta_directa')
        
        # Verificar específicamente el producto problemático (código 10961)
        from farmacia.models import Medicamento
        try:
            med_problematico = Medicamento.objects.get(codigo='10961')
            producto_10961 = [item for item in carrito_raw if item.get('medicamento_id') == med_problematico.id]
            if producto_10961:
                print(f"\n🔴 PRODUCTO 10961 ENCONTRADO:")
                for i, item in enumerate(producto_10961):
                    print(f"    Aparición {i+1}: ID={item.get('medicamento_id')}, Cantidad={item.get('cantidad')}, Nombre={item.get('nombre')}")
        except Medicamento.DoesNotExist:
            print(f"ℹ️ Producto 10961 no encontrado en BD")
        
        # ============================================
        # AGRUPAR ITEMS POR MEDICAMENTO (SOLUCIÓN)
        # ============================================
        items_agrupados = {}
        for item in carrito_raw:
            medicamento_id = item.get('medicamento_id')
            cantidad = int(item.get('cantidad', 1))
            nombre = item.get('nombre', '')
            precio = float(item.get('precio', 0))
            stock = int(item.get('stock', 0))
            principio = item.get('principio_activo', '')
            
            if cantidad <= 0:
                continue
                
            if medicamento_id in items_agrupados:
                # Si ya existe, sumar cantidades
                items_agrupados[medicamento_id]['cantidad'] += cantidad
                print(f"⚠️ DUPLICADO DETECTADO: Medicamento {medicamento_id} - sumando {cantidad} a {items_agrupados[medicamento_id]['cantidad']}")
            else:
                # Si no existe, crear nuevo item
                items_agrupados[medicamento_id] = {
                    'medicamento_id': medicamento_id,
                    'nombre': nombre,
                    'precio': precio,
                    'stock': stock,
                    'cantidad': cantidad,
                    'principio_activo': principio
                }
        
        # Convertir el diccionario agrupado a lista
        carrito = list(items_agrupados.values())
        print(f"\n📊 RESULTADO DE AGRUPACIÓN:")
        print(f"   Items originales: {len(carrito_raw)}")
        print(f"   Items agrupados: {len(carrito)}")
        
        # Mostrar items después de agrupar
        print(f"\n📦 ITEMS A PROCESAR:")
        for i, item in enumerate(carrito):
            print(f"  Item {i}: ID={item['medicamento_id']}, Nombre={item['nombre']}, Cantidad={item['cantidad']}")
        
        # Obtener datos del formulario
        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')
        descuento_str = request.POST.get('descuento', '0')
        observaciones = request.POST.get('observaciones', '')
        
        print(f"\n💰 Datos de pago:")
        print(f"   Método: {metodo_pago}")
        print(f"   Descuento: {descuento_str}")
        print(f"   Observaciones: {observaciones}")
        
        # Validar y convertir descuento
        from decimal import Decimal
        try:
            descuento = Decimal(descuento_str) if descuento_str else Decimal('0')
        except:
            descuento = Decimal('0')
        
        # CALCULAR TOTAL Y CREAR DETALLES
        total = Decimal('0')
        detalles_a_crear = []
        
        for item in carrito:
            medicamento_id = item.get('medicamento_id')
            cantidad = item.get('cantidad')
            
            try:
                medicamento = Medicamento.objects.get(id=medicamento_id, activo=True)
                
                print(f"\n🔍 Verificando medicamento ID {medicamento_id}: {medicamento.nombre_comercial}")
                print(f"   Stock actual: {medicamento.stock_actual}")
                print(f"   Cantidad a vender: {cantidad}")
                
                # Verificar stock
                if medicamento.stock_actual < cantidad:
                    print(f"   ❌ STOCK INSUFICIENTE")
                    if is_ajax:
                        from django.http import JsonResponse
                        return JsonResponse({'success': False, 'error': f'Stock insuficiente: {medicamento.nombre_comercial}'})
                    else:
                        messages.error(request, f'Stock insuficiente: {medicamento.nombre_comercial}')
                        return redirect('farmacia:venta_directa')
                
                # Calcular subtotal
                precio = medicamento.precio_venta
                subtotal = precio * cantidad
                total += subtotal
                
                print(f"   ✅ Stock suficiente")
                print(f"   Precio: {precio}")
                print(f"   Subtotal: {subtotal}")
                
                # Preparar detalle para crear
                detalles_a_crear.append({
                    'medicamento': medicamento,
                    'cantidad': cantidad,
                    'precio_unitario': precio,
                    'subtotal': subtotal
                })
                
            except Medicamento.DoesNotExist:
                print(f"   ❌ Medicamento no encontrado: ID {medicamento_id}")
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': f'Medicamento no encontrado: ID {medicamento_id}'})
                else:
                    messages.error(request, f'Medicamento no encontrado: ID {medicamento_id}')
                continue
        
        if not detalles_a_crear:
            print(f"❌ No hay items válidos en el carrito")
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': 'No hay items válidos en el carrito'})
            else:
                messages.error(request, 'No hay items válidos en el carrito')
                return redirect('farmacia:venta_directa')
        
        # Aplicar descuento
        total_final = total - descuento
        if total_final < 0:
            total_final = Decimal('0')
        
        print(f"\n💰 TOTALES:")
        print(f"   Subtotal: {total}")
        print(f"   Descuento: {descuento}")
        print(f"   Total final: {total_final}")
        
        # CREAR VENTA EN UNA TRANSACCIÓN
        from django.db import transaction
        from farmacia.models import Venta, DetalleVenta, MovimientoInventario
        
        try:
            with transaction.atomic():
                print(f"\n💾 INICIANDO TRANSACCIÓN")
                
                # Crear venta
                venta = Venta.objects.create(
                    total=total_final,
                    descuento=descuento,
                    metodo_pago=metodo_pago,
                    observaciones=f"VENTA EXTERNA - {observaciones}",
                    usuario=request.user
                )
                print(f"   ✅ Venta #{venta.id} creada")
                
                # Crear detalles
                for detalle_data in detalles_a_crear:
                    medicamento = detalle_data['medicamento']
                    cantidad = detalle_data['cantidad']
                    
                    print(f"\n   Procesando {medicamento.nombre_comercial}:")
                    print(f"      Stock antes: {medicamento.stock_actual}")
                    
                    # Actualizar stock
                    # medicamento.stock_actual -= cantidad
                    # medicamento.save()
                    
                    detalle = DetalleVenta.objects.create(
                        venta=venta,
                        medicamento=medicamento,
                        cantidad=cantidad,
                        precio_unitario=detalle_data['precio_unitario'],
                        subtotal=detalle_data['subtotal']
                    )
                    print(f"      ✅ Detalle creado")
                    
                    # Registrar movimiento
                    movimiento = MovimientoInventario.objects.create(
                        medicamento=medicamento,
                        tipo='VENTA',
                        cantidad=cantidad,
                        usuario=request.user,
                        referencia=f'Venta Directa #{venta.id}',
                        precio_unitario=detalle_data['precio_unitario'],
                        venta=venta
                    )
                    print(f"      ✅ Movimiento registrado")
                    print(f"      Stock después: {medicamento.stock_actual}")
                
                # LIMPIAR CARRITO
                if 'carrito_venta_directa' in request.session:
                    del request.session['carrito_venta_directa']
                    request.session.modified = True
                    print(f"\n✅ Carrito limpiado de la sesión")
                
                print(f"\n{'='*60}")
                print(f"✅ VENTA #{venta.id} PROCESADA EXITOSAMENTE")
                print(f"{'='*60}")
                
                # ============================================
                # RESPUESTA SEGÚN EL TIPO DE PETICIÓN
                # ============================================
                if is_ajax:
                    from django.http import JsonResponse
                    from django.urls import reverse
                    print(f"📡 Respondiendo con JSON para AJAX")
                    return JsonResponse({
                        'success': True,
                        'venta_id': venta.id,
                        'message': f'Venta #{venta.id} procesada exitosamente',
                        'redirect_url': reverse('farmacia:ticket_venta', args=[venta.id])
                    })
                else:
                    print(f"📡 Respondiendo con redirect normal")
                    messages.success(request, f'Venta #{venta.id} procesada exitosamente')
                    return redirect('farmacia:ticket_venta', id=venta.id)
                
        except Exception as e:
            print(f"\n❌ ERROR EN TRANSACCIÓN: {str(e)}")
            import traceback
            traceback.print_exc()
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error en transacción: {str(e)}')
                return redirect('farmacia:venta_directa')
            
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, f'Error general: {str(e)}')
            return redirect('farmacia:venta_directa')

####################
@login_required
def ticket_venta(request, id):
    """Muestra el ticket de una venta"""
    venta = get_object_or_404(Venta, id=id)
    detalles = DetalleVenta.objects.filter(venta=venta)

    context = {
        'venta': venta,
        'detalles': detalles,
        'titulo': f'Ticket Venta #{venta.id}'
    }

    return render(request, 'farmacia/ticket_venta.html', context)

# ==============================================
# VISTAS DE PAGOS
# ==============================================
@login_required
@grupo_requerido('farmacia', 'administrador')
@never_cache
def procesar_pago(request, consulta_id):
    """Procesa el pago de recetas seleccionadas"""
    from consultas.models import Consulta

    if request.method == 'POST':
        try:
            consulta = get_object_or_404(Consulta, id=consulta_id)

            # Obtener recetas seleccionadas
            items = []
            index = 0
            while True:
                receta_id = request.POST.get(f'recetas[{index}][receta_id]')
                if not receta_id:
                    break

                cantidad = int(request.POST.get(f'recetas[{index}][cantidad]', 0))
                
                # 🔴 CORREGIDO: Reemplazar coma por punto antes de convertir
                precio_str = request.POST.get(f'recetas[{index}][precio]', '0')
                precio = float(precio_str.replace(',', '.'))

                if cantidad > 0:
                    # Buscar la receta
                    receta = consulta.recetas.filter(id=receta_id).first()
                    if receta:
                        items.append({
                            'receta': receta,
                            'cantidad': cantidad,
                            'precio': precio,
                            'subtotal': precio * cantidad
                        })

                index += 1

            if not items:
                messages.error(request, 'No se seleccionaron medicamentos')
                return redirect('farmacia:detalle_recetas_consulta', consulta_id=consulta_id)

            # 🔴 CORREGIDO: Reemplazar coma por punto en descuento
            descuento_str = request.POST.get('descuento_aplicado', '0')
            try:
                descuento_aplicado = float(descuento_str.replace(',', '.'))
            except:
                descuento_aplicado = 0.0

            metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

            # Calcular subtotal desde los items
            subtotal_calculado = sum(item['precio'] * item['cantidad'] for item in items)
            total_calculado = subtotal_calculado - descuento_aplicado
            if total_calculado < 0:
                total_calculado = 0

            context = {
                'consulta': consulta,
                'items': items,
                'subtotal': subtotal_calculado,
                'descuento': descuento_aplicado,
                'total': total_calculado,
                'metodo_pago': metodo_pago,
                'titulo': 'Pago de Recetas'
            }

            return render(request, 'farmacia/pago_recetas.html', context)

        except Exception as e:
            messages.error(request, f'Error al procesar pago: {str(e)}')
            return redirect('farmacia:recetas_pendientes')

    # Si no es POST, redirigir
    return redirect('farmacia:detalle_recetas_consulta', consulta_id=consulta_id)
#############
@login_required
@never_cache
def finalizar_pago(request, tipo=None, id=None):
    """Finaliza el pago para consultas - VERSIÓN CORREGIDA (sin recálculo del total y con Decimal)"""

    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        if tipo == 'consulta':
            return redirect('farmacia:detalle_recetas_consulta', consulta_id=id)
        return redirect('farmacia:inicio')

    import logging
    from decimal import Decimal
    logger = logging.getLogger(__name__)
    logger.debug("=== FINALIZAR PAGO ===")
    logger.debug(f"Tipo: {tipo}, ID: {id}")
    logger.debug(f"POST data: {dict(request.POST)}")
    confirmado = request.POST.get('confirmado', 'false')
    logger.debug(f"confirmado raw: {confirmado}")

    if confirmado != 'true':
        messages.info(request, 'Operación cancelada por el usuario')
        logger.debug("Cancelado por el usuario (confirmado != 'true')")
        if tipo == 'consulta':
            return redirect('farmacia:detalle_recetas_consulta', consulta_id=id)
        return redirect('farmacia:inicio')

    logger.debug("Confirmado = true, procesando pago...")

    if tipo == 'consulta':
        from consultas.models import Consulta
        from django.utils import timezone

        try:
            consulta = get_object_or_404(Consulta, id=id)

            # 🔴🔴🔴 CONVERSIÓN SEGURA CON NORMALIZACIÓN DE COMAS Y A DECIMAL 🔴🔴🔴
            try:
                total_final_str = request.POST.get('total_final', '0') or '0'
                total_final = Decimal(total_final_str.replace(',', '.'))
            except:
                total_final = Decimal('0')

            try:
                descuento_str = request.POST.get('descuento_aplicado', '0') or '0'
                descuento = Decimal(descuento_str.replace(',', '.'))
            except:
                descuento = Decimal('0')

            metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

            # Crear la venta con el total ya calculado (subtotal - descuento)
            venta = Venta.objects.create(
                total=total_final,
                descuento=descuento,
                metodo_pago=metodo_pago,
                observaciones=f"VENTA INTERNA - Recetas de Consulta #{consulta.id}",
                usuario=request.user
            )

            recetas_atendidas = []
            index = 0

            while True:
                receta_id = request.POST.get(f'recetas[{index}][receta_id]')
                if not receta_id:
                    break

                try:
                    cantidad = int(request.POST.get(f'recetas[{index}][cantidad]', 0) or 0)
                except:
                    cantidad = 0

                if cantidad > 0:
                    # Buscar la receta (asegurar que pertenece a la consulta)
                    receta = consulta.recetas.filter(id=receta_id).first()
                    if receta:
                        logger.debug(f"Procesando receta ID {receta.id} - {receta.medicamento}")
                        try:
                            palabras = receta.medicamento.split()
                            termino_busqueda = palabras[0] if palabras else receta.medicamento

                            medicamento = Medicamento.objects.filter(
                                Q(nombre_comercial__icontains=termino_busqueda) |
                                Q(principio_activo__icontains=termino_busqueda)
                            ).first()

                            if not medicamento:
                                medicamento = Medicamento.objects.first()
                                logger.debug(f"⚠️ Medicamento no encontrado para '{receta.medicamento}', usando fallback")

                            if medicamento and medicamento.stock_actual >= cantidad:
                                # medicamento.precio_venta es Decimal
                                subtotal = medicamento.precio_venta * cantidad

                                DetalleVenta.objects.create(
                                    venta=venta,
                                    medicamento=medicamento,
                                    cantidad=cantidad,
                                    precio_unitario=medicamento.precio_venta,
                                    subtotal=subtotal
                                )

                                MovimientoInventario.objects.create(
                                    medicamento=medicamento,
                                    tipo='VENTA',
                                    cantidad=cantidad,
                                    usuario=request.user,
                                    referencia=f'Venta receta #{receta.id} - Consulta #{consulta.id}',
                                    precio_unitario=medicamento.precio_venta,
                                    venta=venta
                                )

                                # Actualizar receta
                                receta.cantidad_atendida = cantidad
                                receta.estado = 'ATENDIDA'
                                receta.usuario_atencion = request.user
                                receta.fecha_atencion = timezone.now()
                                receta.observaciones_farmacia = f'Pagado con {metodo_pago}'
                                receta.save()
                                logger.debug(f"✅ Receta {receta.id} actualizada a estado {receta.estado}")

                                recetas_atendidas.append({
                                    'receta': receta,
                                    'cantidad': cantidad,
                                    'medicamento': medicamento,
                                    'subtotal': subtotal
                                })

                                logger.debug(f"✅ Procesado: {medicamento.nombre_comercial} x{cantidad} (subtotal: {subtotal})")

                            else:
                                stock_disponible = medicamento.stock_actual if medicamento else 0
                                messages.warning(
                                    request,
                                    f'Stock insuficiente para {receta.medicamento}. Disponible: {stock_disponible}'
                                )
                                logger.debug(f"Stock insuficiente para receta {receta.id}")

                        except Exception as e:
                            logger.error(f"❌ Error procesando receta {receta.id}: {str(e)}")
                            messages.warning(request, f'Error con {receta.medicamento}: {str(e)}')
                    else:
                        logger.debug(f"❌ Receta ID {receta_id} no encontrada en la consulta {consulta.id}")

                index += 1

            if not recetas_atendidas:
                messages.error(request, 'No se pudo procesar ninguna receta')
                venta.delete()
                return redirect('farmacia:procesar_pago', consulta_id=id)

            # Verificación (ya no modificamos el total)
            from django.db.models import Sum
            suma_subtotales = venta.detalles.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
            logger.debug(f"💰 Suma de subtotales de detalles: {suma_subtotales}")
            logger.debug(f"💰 Total de venta (con descuento): {venta.total}")
            logger.debug(f"💰 Descuento aplicado: {descuento}")
            logger.debug(f"💰 Verificación: suma_subtotales - descuento = {suma_subtotales - descuento}")

            messages.success(
                request,
                f'✅ Pago procesado exitosamente. {len(recetas_atendidas)} producto(s) en la venta #{venta.id}.'
            )
            return redirect('farmacia:ticket_venta', id=venta.id)

        except Exception as e:
            logger.error(f"❌ Error general en finalizar_pago: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'❌ Error al procesar pago: {str(e)}')
            return redirect('farmacia:recetas_pendientes')

    elif tipo == 'venta_directa':
        return redirect('farmacia:ticket_venta', id=id)

    else:
        messages.error(request, 'Tipo de pago no válido')
        return redirect('farmacia:venta_directa')
# VISTAS DE HISTORIAL Y BÚSQUEDAS
# ==============================================

@login_required
@never_cache
def historial_ventas(request):
    """Muestra historial de ventas"""
    # Filtros
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    metodo_pago = request.GET.get('metodo_pago', '')
    
    # Query base
    ventas_qs = Venta.objects.select_related('usuario').order_by('-fecha_hora')
    
   # Aplicar filtros
    if fecha_desde:
        ventas_qs = ventas_qs.filter(fecha_hora__gte=fecha_desde)
    
    if fecha_hasta:
        ventas_qs = ventas_qs.filter(fecha_hora__lte=fecha_hasta)
    
    if metodo_pago:
        ventas_qs = ventas_qs.filter(metodo_pago=metodo_pago)
    
    # Paginación
    paginator = Paginator(ventas_qs, 20)
    page_number = request.GET.get('page')
    ventas = paginator.get_page(page_number)
    
    # Estadísticas
    total_ventas = ventas_qs.count()
    total_monto = ventas_qs.aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'ventas': ventas,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'metodo_pago': metodo_pago,
        'total_ventas': total_ventas,
        'total_monto': total_monto,
        'titulo': 'Historial de Ventas'
    }
    
    return render(request, 'farmacia/historial_ventas.html', context)

@login_required
@never_cache
def detalle_venta(request, id):
    """Muestra detalle de una venta"""
    venta = get_object_or_404(Venta, id=id)
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('medicamento')
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'titulo': f'Detalle Venta #{venta.id}'
    }
    
    return render(request, 'farmacia/detalle_venta.html', context)

# ==============================================
# VISTAS DE BÚSQUEDA AJAX
# ==============================================
@login_required
def buscar_medicamentos_ajax(request):
    """Búsqueda AJAX para venta directa - VERSIÓN CORREGIDA (con soporte para códigos numéricos)"""
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 1:  # Permitir 1 carácter para códigos
        return JsonResponse({'medicamentos': []})

    try:
        # Construir filtro
        filtro = Q(activo=True)
        
        # Si el query es numérico, buscar también por código exacto
        if query.isdigit():
            filtro &= (Q(codigo__exact=query) |  # Búsqueda exacta
                       Q(codigo__icontains=query) |
                       Q(nombre_comercial__icontains=query) |
                       Q(principio_activo__icontains=query))
        else:
            filtro &= (Q(codigo__icontains=query) |
                       Q(nombre_comercial__icontains=query) |
                       Q(principio_activo__icontains=query))
        
        medicamentos = Medicamento.objects.filter(filtro).order_by('nombre_comercial')[:20]

        medicamentos_list = []
        for med in medicamentos:
            medicamentos_list.append({
                'id': med.id,
                'codigo': med.codigo,
                'nombre': med.nombre_comercial,
                'principio_activo': med.principio_activo or '',
                'stock': med.stock_actual,
                'precio': float(med.precio_venta),
                'presentacion': med.forma_farmaceutica or '',
                'tiene_stock': med.stock_actual > 0
            })

        return JsonResponse({'medicamentos': medicamentos_list})

    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return JsonResponse({'medicamentos': [], 'error': str(e)})


########### buscar medicamento
@login_required
def buscar_medicamento_venta(request):
    """Busca medicamentos por código o nombre para venta directa"""
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return JsonResponse({'medicamentos': []})

    try:
        # Búsqueda amplia
        medicamentos = Medicamento.objects.filter(
            Q(activo=True) & (
                Q(codigo__icontains=query) |
                Q(nombre_comercial__icontains=query) |
                Q(nombre_generico__icontains=query) |
                Q(principio_activo__icontains=query) |
                Q(concentracion__icontains=query)
            )
        ).order_by('nombre_comercial')[:20]

        medicamentos_list = []
        for med in medicamentos:
            medicamentos_list.append({
                'id': med.id,
                'codigo': med.codigo,
                'nombre': med.nombre_comercial,
                'principio_activo': med.principio_activo or '',
                'stock': med.stock_actual,
                'precio': float(med.precio_venta),
                'presentacion': str(med.presentacion) if med.presentacion else '',
                'nombre_generico': med.nombre_generico or '',
                'concentracion': med.concentracion or '',
                'activo': med.activo,
                'tiene_stock': med.stock_actual > 0
            })

        return JsonResponse({'medicamentos': medicamentos_list})

    except Exception as e:
        print(f"Error en búsqueda: {str(e)}")
        return JsonResponse({'medicamentos': [], 'error': str(e)})

# ==============================================
# VISTAS PARA GESTIÓN DE CATEGORÍAS
# ==============================================
# ==============================================
# VISTAS PARA GESTIÓN DE CATEGORÍAS
# ==============================================

@login_required
@never_cache
def lista_categorias(request):
    """Lista todas las categorías"""
    categorias = Categoria.objects.all().order_by('nombre')

    context = {
        'categorias': categorias,
        'titulo': 'Categorías de Medicamentos'
    }
    return render(request, 'farmacia/categorias/lista.html', context)

@login_required
@never_cache
def crear_categoria(request):
    """Crea una nueva categoría"""
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Categoría creada exitosamente')
            return redirect('farmacia:lista_categorias')
    else:
        form = CategoriaForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nueva Categoría'
    }
    return render(request, 'farmacia/categorias/crear.html', context)

@login_required
@never_cache
def editar_categoria(request, id):
    """Edita una categoría existente"""
    categoria = get_object_or_404(Categoria, id=id)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Categoría actualizada exitosamente')
            return redirect('farmacia:lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    context = {
        'form': form,
        'categoria': categoria,
        'titulo': f'Editar: {categoria.nombre}'
    }
    return render(request, 'farmacia/categorias/editar.html', context)

# ==============================================
# VISTAS PARA GESTIÓN DE PRESENTACIONES
# ==============================================

@login_required
@never_cache
def lista_presentaciones(request):
    """Lista todas las presentaciones"""
    presentaciones = Presentacion.objects.all().order_by('nombre')

    context = {
        'presentaciones': presentaciones,
        'titulo': 'Presentaciones de Medicamentos'
    }
    return render(request, 'farmacia/presentaciones/lista.html', context)

@login_required
@never_cache
def crear_presentacion(request):
    """Crea una nueva presentación"""
    if request.method == 'POST':
        form = PresentacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Presentación creada exitosamente')
            return redirect('farmacia:lista_presentaciones')
    else:
        form = PresentacionForm()

    context = {
        'form': form,
        'titulo': 'Registrar Nueva Presentación'
    }
    return render(request, 'farmacia/presentaciones/crear.html', context)

@login_required
@never_cache
def editar_presentacion(request, id):
    """Edita una presentación existente"""
    presentacion = get_object_or_404(Presentacion, id=id)

    if request.method == 'POST':
        form = PresentacionForm(request.POST, instance=presentacion)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Presentación actualizada exitosamente')
            return redirect('farmacia:lista_presentaciones')
    else:
        form = PresentacionForm(instance=presentacion)

    context = {
        'form': form,
        'presentacion': presentacion,
        'titulo': f'Editar: {presentacion.nombre}'
    }
    return render(request, 'farmacia/presentaciones/editar.html', context)

######## actualizar carro
# Agregar en views.py

@login_required
def actualizar_carrito(request):
    """Actualiza el carrito en la sesión desde el frontend"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            carrito_data = data.get('carrito', {})

            # Convertir objeto JavaScript a lista para Django
            carrito_lista = []
            for item_id, item_data in carrito_data.items():
                carrito_lista.append({
                    'medicamento_id': int(item_id),
                    'nombre': item_data.get('nombre', ''),
                    'precio': float(item_data.get('precio', 0)),
                    'cantidad': int(item_data.get('cantidad', 1)),
                    'stock': int(item_data.get('stock', 0)),
                    'principio_activo': item_data.get('principio_activo', ''),
                    'seleccionado': bool(item_data.get('seleccionado', True))
                })

            # Guardar en sesión
            request.session['carrito_venta_directa'] = carrito_lista
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': f'Carrito actualizado: {len(carrito_lista)} items'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

@login_required
def obtener_carrito(request):
    """Devuelve el carrito actual desde la sesión"""
    carrito = request.session.get('carrito_venta_directa', [])
    return JsonResponse({'carrito': carrito})

########### combos topico ###########

###########################

@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_combo_carrito(request, combo_id):
    """
    Agrega un combo completo al carrito de tópico con validación de stock
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        combo = ComboTopico.objects.get(id=combo_id, activo=True)
        
        # Validar stock de todos los medicamentos del combo
        for item in combo.medicamentos.all():
            if item.medicamento.stock_actual < item.cantidad:  # Ajusta campo de stock
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente para {item.medicamento.nombre_comercial}'
                })
        
        # Inicializar carrito
        if 'carrito_topico' not in request.session:
            request.session['carrito_topico'] = {
                'items': [],
                'total': 0
            }
        
        carrito = request.session['carrito_topico']
        
        # Calcular total del combo
        total_combo = float(combo.calcular_precio_total())
        
        # Agregar combo al carrito
        item_id = f"combo_{combo.id}_{len(carrito['items'])}"
        
        # Obtener detalles de medicamentos
        medicamentos_detalle = []
        for cm in combo.medicamentos.all():
            medicamentos_detalle.append({
                'medicamento_id': cm.medicamento.id,
                'nombre': cm.medicamento.nombre_comercial,
                'cantidad': cm.cantidad,
                'precio_unitario': float(cm.medicamento.precio_venta),
                'subtotal': float(cm.subtotal())
            })
        
        carrito['items'].append({
            'item_id': item_id,
            'tipo': 'combo',
            'combo_id': combo.id,
            'nombre': combo.nombre,
            'medicamentos': medicamentos_detalle,
            'subtotal': total_combo,
        })
        
        # Recalcular total
        carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Combo "{combo.nombre}" agregado',
            'carrito': carrito
        })
        
    except ComboTopico.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Combo no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
###########################
@login_required
@grupo_requerido('farmacia', 'administrador')
def ver_carrito_topico(request):
    """
    Muestra el contenido del carrito de tópico
    """
    carrito = request.session.get('carrito_topico', {
        'items': [],
        'mano_obra': 0,
        'total': 0
    })

    context = {
        'carrito': carrito,
        'titulo': 'Carrito de Tópico',
    }
    return render(request, 'farmacia/carrito_topico.html', context)


@login_required
@grupo_requerido('farmacia', 'administrador')
def eliminar_item_carrito(request, item_id):
    """
    Elimina un item del carrito de tópico
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    carrito = request.session.get('carrito_topico', {'items': []})

    # Filtrar items eliminando el que coincide
    carrito['items'] = [item for item in carrito['items'] if item.get('item_id') != item_id]

    # Recalcular total
    carrito['total'] = sum(item['subtotal'] for item in carrito['items']) + carrito.get('mano_obra', 0)
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'carrito': carrito
    })

################ combo topico #####
@login_required
@grupo_requerido('farmacia', 'administrador')
def lista_combos(request):
    """
    Muestra todos los combos disponibles y procedimientos de tópico
    """
    # Importar modelo de tópicos
    from consultas.models import TopicoCatalogo

    # Obtener combos
    combos = ComboTopico.objects.filter(activo=True).prefetch_related('medicamentos__medicamento')

    # 🔥 OBTENER TÓPICOS (esto es lo que faltaba)
    topicos = TopicoCatalogo.objects.filter(activo=True).order_by('nombre')

    print(f"\n===== DEPURACIÓN =====")
    print(f"Combos encontrados: {combos.count()}")
    print(f"Tópicos encontrados: {topicos.count()}")

    combos_data = []
    for combo in combos:
        medicamentos_lista = []
        for item in combo.medicamentos.all():
            medicamentos_lista.append({
                'nombre': item.medicamento.nombre_comercial,
                'cantidad': item.cantidad,
                'precio': float(item.medicamento.precio_venta),
                'subtotal': float(item.subtotal())
            })

        combos_data.append({
            'id': combo.id,
            'nombre': combo.nombre,
            'descripcion': combo.descripcion,
            'medicamentos': medicamentos_lista,
            'precio_total': float(combo.calcular_precio_total()),
        })

    context = {
        'combos': combos_data,
        'topicos': topicos,  # 👈 AHORA SÍ ESTÁN LOS TÓPICOS
        'titulo': 'Tópico - Procedimientos y Combos',
    }
    return render(request, 'farmacia/lista_combos.html', context)

####################
@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_combo_carrito(request, combo_id):
    """
    Agrega un combo completo al carrito de tópico con validación de stock
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        combo = ComboTopico.objects.get(id=combo_id, activo=True)
        
        # 🔥 VALIDAR STOCK de todos los medicamentos del combo
        for item in combo.medicamentos.all():
            if item.medicamento.stock_actual < item.cantidad:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente para {item.medicamento.nombre_comercial}. Disponible: {item.medicamento.stock_actual}, Requerido: {item.cantidad}'
                })
        
        # Inicializar carrito si no existe
        if 'carrito_topico' not in request.session:
            request.session['carrito_topico'] = {
                'items': [],
                'total': 0
            }
        
        carrito = request.session['carrito_topico']
        
        # Calcular total del combo
        total_combo = float(combo.calcular_precio_total())
        
        # Generar ID único para el item
        item_id = f"combo_{combo.id}_{len(carrito['items'])}"
        
        # Obtener detalles de medicamentos
        medicamentos_detalle = []
        for cm in combo.medicamentos.all():
            medicamentos_detalle.append({
                'medicamento_id': cm.medicamento.id,
                'nombre': cm.medicamento.nombre_comercial,
                'cantidad': cm.cantidad,
                'precio_unitario': float(cm.medicamento.precio_venta),
                'subtotal': float(cm.subtotal())
            })
        
        carrito['items'].append({
            'item_id': item_id,
            'tipo': 'combo',  # 👈 IMPORTANTE: debe ser 'combo', no 'mano_obra'
            'combo_id': combo.id,
            'nombre': combo.nombre,
            'medicamentos': medicamentos_detalle,
            'subtotal': total_combo,
        })
        
        # Recalcular total
        carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Combo "{combo.nombre}" agregado',
            'carrito': carrito
        })
        
    except ComboTopico.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Combo no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
####################
@login_required
@grupo_requerido('farmacia', 'administrador')
def ver_carrito_topico(request):
    """
    Muestra el contenido del carrito de tópico
    """
    carrito = request.session.get('carrito_topico', {
        'items': [],
        'mano_obra': 0,
        'total': 0
    })

    context = {
        'carrito': carrito,
        'titulo': 'Carrito de Tópico',
    }
    return render(request, 'farmacia/carrito_topico.html', context)



#############################

@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_mano_obra_carrito(request, mano_obra_id):
    """
    Agrega un item de mano de obra al carrito de tópico
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        mano_obra = TopicoManoObra.objects.get(id=mano_obra_id, activo=True)

        # Inicializar carrito si no existe
        if 'carrito_topico' not in request.session:
            request.session['carrito_topico'] = {
                'items': [],
                'total': 0
            }

        carrito = request.session['carrito_topico']

        # Agregar mano de obra al carrito
        item_id = f"mano_obra_{mano_obra.id}"

        # Verificar si ya existe
        exists = False
        for item in carrito['items']:
            if item.get('item_id') == item_id:
                exists = True
                break

        if not exists:
            carrito['items'].append({
                'item_id': item_id,
                'tipo': 'mano_obra',
                'mano_obra_id': mano_obra.id,
                'nombre': mano_obra.nombre,
                'descripcion': mano_obra.descripcion,
                'precio': float(mano_obra.precio),
                'subtotal': float(mano_obra.precio),
            })

            # Recalcular total
            carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
            request.session.modified = True

            return JsonResponse({
                'success': True,
                'message': f'✅ Mano de obra "{mano_obra.nombre}" agregada',
                'carrito': carrito
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Este servicio ya está en el carrito'
            })

    except TopicoManoObra.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Servicio no encontrado'})

    ######################
@login_required
@grupo_requerido('farmacia', 'administrador')
def obtener_carrito_topico(request):
    """
    Devuelve el contenido actual del carrito de tópico
    """
    carrito = request.session.get('carrito_topico', {'items': [], 'total': 0})
    return JsonResponse({'carrito': carrito})

#################
@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_topico_carrito(request):
    """
    Agrega un procedimiento de tópico al carrito
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    import json
    data = json.loads(request.body)
    
    # Inicializar carrito
    if 'carrito_topico' not in request.session:
        request.session['carrito_topico'] = {
            'items': [],
            'total': 0
        }
    
    carrito = request.session['carrito_topico']
    
    # Crear item de tópico
    item_id = f"topico_{data['topico_id']}_{len(carrito['items'])}"
    
    carrito['items'].append({
        'item_id': item_id,
        'tipo': 'topico',  # Cambiado de 'mano_obra' a 'topico'
        'topico_id': data['topico_id'],
        'nombre': data['nombre'],
        'precio': data['precio'],
        'subtotal': data['precio']
    })
    
    # Recalcular total
    carrito['total'] = sum(item['subtotal'] for item in carrito['items'])
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'message': f'✅ {data["nombre"]} agregado - S/ {data["precio"]:.2f}',
        'carrito': carrito
    })

#########################
@login_required
@grupo_requerido('farmacia', 'administrador')
def procesar_venta_topico(request):
    """
    Procesa la venta del carrito de tópico y genera ticket
    VERSIÓN CORREGIDA - CON MOVIMIENTOS DE INVENTARIO
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    carrito = request.session.get('carrito_topico', {'items': [], 'total': 0})
    
    if not carrito['items']:
        return JsonResponse({'success': False, 'error': 'Carrito vacío'})
    
    try:
        from .models import Venta, DetalleVenta, Medicamento, MovimientoInventario
        from django.db import transaction
        
        with transaction.atomic():
            # Validar stock para combos
            for item in carrito['items']:
                if item['tipo'] == 'combo':
                    for med in item.get('medicamentos', []):
                        medicamento = Medicamento.objects.select_for_update().get(id=med['medicamento_id'])
                        if medicamento.stock_actual < med['cantidad']:
                            return JsonResponse({
                                'success': False,
                                'error': f'Stock insuficiente para {med["nombre"]}'
                            })
            
            # Crear venta
            venta = Venta.objects.create(
                total=carrito['total'],
                descuento=0,
                metodo_pago='EFECTIVO',
                usuario=request.user,
                observaciones='VENTA INTERNA - Tópico'  # 🔥 PREFIJO ESTÁNDAR
            )
            
            # Procesar items
            for item in carrito['items']:
                if item['tipo'] == 'combo':
                    # Es un combo: descontar stock de cada medicamento
                    for med in item.get('medicamentos', []):
                        medicamento = Medicamento.objects.get(id=med['medicamento_id'])
                        
                        # Crear detalle de venta
                        DetalleVenta.objects.create(
                            venta=venta,
                            medicamento=medicamento,
                            cantidad=med['cantidad'],
                            precio_unitario=med['precio_unitario'],
                            subtotal=med['subtotal']
                        )
                        
                        # ✅ REGISTRAR MOVIMIENTO DE INVENTARIO (CADA MEDICAMENTO)
                        MovimientoInventario.objects.create(
                            medicamento=medicamento,
                            tipo='VENTA',
                            cantidad=med['cantidad'],
                            usuario=request.user,
                            referencia=f'Venta Tópico - Combo {item["nombre"]} - Venta #{venta.id}',
                            precio_unitario=med['precio_unitario'],
                            venta=venta
                        )
                        # ❌ ELIMINADO: medicamento.stock_actual -= med['cantidad']
                        # ❌ ELIMINADO: medicamento.save()
                        # El stock se actualiza SOLO en el save() del movimiento
                        
                else:  # item['tipo'] == 'topico' (mano de obra)
                    # Es mano de obra: NO descontar stock, solo registrar
                    DetalleVenta.objects.create(
                        venta=venta,
                        medicamento=None,
                        descripcion=item['nombre'],
                        cantidad=1,
                        precio_unitario=item['precio'],
                        subtotal=item['precio']
                    )
                    # No hay movimiento de inventario porque no es medicamento
            
            # Limpiar carrito
            del request.session['carrito_topico']
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'venta_id': venta.id,
                'message': 'Venta procesada correctamente'
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)})

######### ticket combo
@login_required
@grupo_requerido('farmacia', 'administrador')
def ticket_topico(request, venta_id):
    """
    Muestra el ticket de venta de tópico
    """
    from .models import Venta
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.all()

    context = {
        'venta': venta,
        'detalles': detalles,
        'fecha': timezone.now(),
        'usuario': request.user,
    }
    return render(request, 'farmacia/ticket_topico.html', context)


############## lista compras #############
# ==============================================
# COMPRAS A PROVEEDORES (NUEVO MÓDULO)
# ==============================================

@login_required
@grupo_requerido('farmacia', 'administrador')
def lista_compras(request):
    """Listar todas las compras realizadas con filtros"""
    from django.db.models import Q
    from django.core.paginator import Paginator
    
    compras = Compra.objects.select_related('proveedor', 'usuario').order_by('-fecha_compra')
    
    # 🔍 FILTRO POR NÚMERO DE FACTURA
    query = request.GET.get('q', '')
    if query:
        compras = compras.filter(numero_factura__icontains=query)
    
    # FILTRO POR PROVEEDOR
    proveedor_id = request.GET.get('proveedor')
    if proveedor_id:
        compras = compras.filter(proveedor_id=proveedor_id)
    
    # Paginación
    paginator = Paginator(compras, 20)
    page = request.GET.get('page', 1)
    compras_page = paginator.get_page(page)
    
    context = {
        'compras': compras_page,
        'proveedores': Proveedor.objects.filter(activo=True),
        'proveedor_id': proveedor_id,
        'query': query,  # 👈 NUEVO
        'titulo': 'Historial de Compras'
    }
    return render(request, 'farmacia/lista_compras.html', context)


@login_required
@grupo_requerido('farmacia', 'administrador')
def registrar_compra(request):
    """Página principal para registrar compras (Excel o manual)"""
    preview_items = request.session.get('preview_items', None)
    errores = request.session.get('errores_carga', [])
    
    context = {
        'proveedores': Proveedor.objects.filter(activo=True).order_by('nombre'),
        'titulo': 'Registrar Compra a Proveedor',
        'preview_items': preview_items,
        'errores': errores,
        'today': date.today(),
    }
    return render(request, 'farmacia/registrar_compra.html', context)


@login_required
@grupo_requerido('farmacia', 'administrador')
def finalizar_compra_excel(request):
    """Finaliza la compra masiva desde Excel con datos de factura"""
    from decimal import Decimal
    from datetime import datetime
    from django.db import transaction
    
    if request.method != 'POST':
        return redirect('farmacia:registrar_compra')
    
    proveedor_id = request.POST.get('proveedor_id')
    numero_factura = request.POST.get('numero_factura')
    fecha_factura = request.POST.get('fecha_factura')
    incluye_igv = request.POST.get('incluye_igv') == 'on'
    factura_pagada = request.POST.get('factura_pagada') == 'on'
    
    if not proveedor_id or not numero_factura or not fecha_factura:
        messages.error(request, 'Complete todos los datos de la factura')
        return redirect('farmacia:registrar_compra')
    
    items = request.session.get('preview_items', [])
    if not items:
        items = request.session.get('previsualizacion_compra', {}).get('items', [])
    
    if not items:
        messages.error(request, 'No hay productos cargados. Suba el Excel primero.')
        return redirect('farmacia:registrar_compra')
    
    try:
        with transaction.atomic():
            proveedor = get_object_or_404(Proveedor, id=proveedor_id)
            
            subtotal = Decimal(str(sum(item['subtotal'] for item in items)))
            
            if incluye_igv:
                igv = subtotal * Decimal('0.18')
                total = subtotal + igv
            else:
                igv = Decimal('0')
                total = subtotal
            
            observaciones = ''
            if factura_pagada:
                observaciones += ' [FACTURA PAGADA]'
            else:
                observaciones += ' [FACTURA PENDIENTE]'
            
            compra = Compra.objects.create(
                proveedor=proveedor,
                numero_factura=numero_factura,
                fecha_factura=fecha_factura,
                subtotal=subtotal,
                igv=igv,
                total=total,
                observaciones=observaciones,
                usuario=request.user
            )
            
            for item in items:
                medicamento = get_object_or_404(Medicamento, id=item['medicamento_id'])
                
                DetalleCompra.objects.create(
                    compra=compra,
                    medicamento=medicamento,
                    cantidad=item['cantidad'],
                    precio_unitario=Decimal(str(item['precio_unitario'])),
                    lote=item['lote'],
                    fecha_vencimiento=datetime.strptime(item['fecha_vencimiento'], '%d/%m/%Y').date(),
                    subtotal=Decimal(str(item['subtotal']))
                )
                
                medicamento.precio_compra = Decimal(str(item['precio_unitario']))
                medicamento.lote = item['lote']
                medicamento.fecha_vencimiento = datetime.strptime(item['fecha_vencimiento'], '%d/%m/%Y').date()
                medicamento.save()
                
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo='COMPRA',
                    cantidad=item['cantidad'],
                    usuario=request.user,
                    referencia=f'Compra #{compra.id} - {numero_factura}',
                    precio_unitario=Decimal(str(item['precio_unitario']))
                )
            
            request.session.pop('preview_items', None)
            request.session.pop('previsualizacion_compra', None)
            
            messages.success(request, f'✅ Compra #{compra.id} registrada con {len(items)} productos.')
            return redirect('farmacia:detalle_compra', compra_id=compra.id)
            
    except Exception as e:
        messages.error(request, f'Error al finalizar compra: {str(e)}')
        return redirect('farmacia:registrar_compra')



@login_required
@grupo_requerido('farmacia', 'administrador')
def descargar_plantilla_compra(request):
    """Descargar plantilla Excel para carga masiva de compras"""
    import pandas as pd
    from io import BytesIO
    from django.http import HttpResponse

    # Crear DataFrame vacío solo con encabezados
    data = {
        'Código': [],
        'Cantidad': [],
        'Lote': [],
        'Vencimiento': [],
        'Precio Unit.': [],
    }

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Compra', index=False)
        worksheet = writer.sheets['Compra']
        for column in df:
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = 18

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_compra.xlsx"'

    return response

#########################################
@login_required
@grupo_requerido('farmacia', 'administrador')
def cargar_compra_excel(request):
    """Carga Excel con compras - Versión simplificada con formulario de factura"""
    import pandas as pd
    from datetime import datetime
    from decimal import Decimal
    
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        
        try:
            df = pd.read_excel(archivo)
            
            columnas_obligatorias = ['Código', 'Cantidad', 'Lote', 'Vencimiento', 'Precio Unit.']
            for col in columnas_obligatorias:
                if col not in df.columns:
                    messages.error(request, f'La columna obligatoria "{col}" no está en el Excel')
                    return redirect('farmacia:registrar_compra')
            
            items_preview = []
            errores = []
            
            for idx, row in df.iterrows():
                try:
                    codigo = str(row['Código']).strip()
                    
                    try:
                        medicamento = Medicamento.objects.get(codigo=codigo, activo=True)
                        nombre = medicamento.nombre_comercial
                        medicamento_id = medicamento.id
                        es_nuevo = False
                    except Medicamento.DoesNotExist:
                        errores.append(f"Fila {idx+2}: Código '{codigo}' no encontrado")
                        continue
                    
                    cantidad = int(row['Cantidad'])
                    lote = str(row['Lote']).strip()
                    
                    try:
                        if isinstance(row['Vencimiento'], datetime):
                            fecha_venc = row['Vencimiento'].date()
                        else:
                            fecha_venc = pd.to_datetime(row['Vencimiento']).date()
                    except:
                        errores.append(f"Fila {idx+2}: Fecha de vencimiento inválida")
                        continue
                    
                    precio_compra = float(row['Precio Unit.'])
                    
                    items_preview.append({
                        'codigo': codigo,
                        'nombre': nombre,
                        'medicamento_id': medicamento_id,
                        'cantidad': cantidad,
                        'lote': lote,
                        'fecha_vencimiento': fecha_venc.strftime('%d/%m/%Y'),
                        'precio_unitario': precio_compra,
                        'subtotal': round(cantidad * precio_compra, 2),
                        'es_nuevo': False,
                    })
                    
                except Exception as e:
                    errores.append(f"Fila {idx+2}: {str(e)}")
            
            if not items_preview:
                messages.error(request, 'No se encontraron items válidos')
                return redirect('farmacia:registrar_compra')
            
            # Guardar en sesión
            request.session['preview_items'] = items_preview
            request.session['errores_carga'] = errores
            
            messages.success(request, f'✅ {len(items_preview)} productos cargados. Complete los datos de la factura.')
            return redirect('farmacia:registrar_compra')
            
        except Exception as e:
            messages.error(request, f'Error al leer archivo: {str(e)}')
            return redirect('farmacia:registrar_compra')
    
    return redirect('farmacia:registrar_compra')
##########################

#############################
@login_required
def detalle_compra(request, compra_id):
    """Ver detalle de una compra registrada"""
    compra = get_object_or_404(Compra.objects.select_related('proveedor', 'usuario'), id=compra_id)
    detalles = compra.detalles.select_related('medicamento').all()  # 👈 ESTO ES CLAVE
    
    context = {
        'compra': compra,
        'detalles': detalles,  # 👈 DEBE PASARSE AL TEMPLATE
        'titulo': f'Compra #{compra.id} - {compra.numero_factura}'
    }
    return render(request, 'farmacia/detalle_compra.html', context)

##################
@login_required
@grupo_requerido('farmacia', 'administrador')
def compra_manual(request):
    """Registro manual de compra (producto por producto)"""
    
    # Inicializar carrito en sesión si no existe
    if 'carrito_compra' not in request.session:
        request.session['carrito_compra'] = {
            'items': [],
            'subtotal': 0,
            'igv': 0,
            'total': 0,
            'incluye_igv': False
        }
    
    context = {
        'proveedores': Proveedor.objects.filter(activo=True).order_by('nombre'),
        'carrito': request.session['carrito_compra'],
        'titulo': 'Registrar Compra Manual'
    }
    return render(request, 'farmacia/compra_manual.html', context)

    #############

@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_item_compra(request):
    """Agrega un producto al carrito de compra manual con cálculo inteligente"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        
        # Obtener medicamento
        medicamento_id = data.get('medicamento_id')
        if not medicamento_id:
            return JsonResponse({'success': False, 'error': 'Debe seleccionar un medicamento'})
        
        medicamento = get_object_or_404(Medicamento, id=medicamento_id, activo=True)
        
        # Obtener valores
        cantidad = data.get('cantidad')
        precio_unitario = data.get('precio_unitario')
        subtotal = data.get('subtotal')
        lote = data.get('lote', '').strip()
        fecha_vencimiento = data.get('fecha_vencimiento')
        
        # Validar que haya al menos 2 de 3 valores
        valores_presentes = sum([
            1 if cantidad not in [None, ''] else 0,
            1 if precio_unitario not in [None, ''] else 0,
            1 if subtotal not in [None, ''] else 0
        ])
        
        if valores_presentes < 2:
            return JsonResponse({
                'success': False, 
                'error': 'Debe ingresar al menos 2 valores: cantidad, precio unitario o subtotal'
            })
        
        # Convertir a float para cálculos
        cantidad = float(cantidad) if cantidad not in [None, ''] else None
        precio_unitario = float(precio_unitario) if precio_unitario not in [None, ''] else None
        subtotal = float(subtotal) if subtotal not in [None, ''] else None
        
        # Calcular el valor faltante
        if cantidad is not None and precio_unitario is not None:
            subtotal = cantidad * precio_unitario
        elif cantidad is not None and subtotal is not None:
            precio_unitario = subtotal / cantidad
        elif precio_unitario is not None and subtotal is not None:
            cantidad = subtotal / precio_unitario
        else:
            return JsonResponse({'success': False, 'error': 'No se pudo calcular el valor faltante'})
        
        # Validar lote y fecha
        if not lote:
            return JsonResponse({'success': False, 'error': 'El lote es obligatorio'})
        
        if not fecha_vencimiento:
            return JsonResponse({'success': False, 'error': 'La fecha de vencimiento es obligatoria'})
        
        from datetime import datetime
        fecha_venc = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
        
        # Crear item
        item = {
            'id': len(request.session['carrito_compra']['items']) + 1,
            'medicamento_id': medicamento.id,
            'codigo': medicamento.codigo,
            'nombre': medicamento.nombre_comercial,
            'cantidad': cantidad,
            'lote': lote,
            'fecha_vencimiento': fecha_vencimiento,
            'precio_unitario': round(precio_unitario, 2),
            'subtotal': round(subtotal, 2)
        }
        
        # Agregar al carrito
        request.session['carrito_compra']['items'].append(item)
        
        # Recalcular totales
        carrito = request.session['carrito_compra']
        subtotal_total = sum(i['subtotal'] for i in carrito['items'])
        carrito['subtotal'] = subtotal_total
        
        if carrito.get('incluye_igv', False):
            carrito['igv'] = subtotal_total * 0.18
            carrito['total'] = subtotal_total + carrito['igv']
        else:
            carrito['igv'] = 0
            carrito['total'] = subtotal_total
        
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'item': item,
            'carrito': carrito
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

        ####################
@login_required
@grupo_requerido('farmacia', 'administrador')
def eliminar_item_compra(request, item_id):
    """Elimina un producto del carrito de compra manual"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    carrito = request.session.get('carrito_compra', {'items': []})
    
    # Filtrar items
    carrito['items'] = [i for i in carrito['items'] if i['id'] != item_id]
    
    # Recalcular totales
    subtotal_total = sum(i['subtotal'] for i in carrito['items'])
    carrito['subtotal'] = subtotal_total
    
    if carrito.get('incluye_igv', False):
        carrito['igv'] = subtotal_total * 0.18
        carrito['total'] = subtotal_total + carrito['igv']
    else:
        carrito['igv'] = 0
        carrito['total'] = subtotal_total
    
    request.session.modified = True
    
    return JsonResponse({'success': True, 'carrito': carrito})

###################
@login_required
@grupo_requerido('farmacia', 'administrador')
def confirmar_compra(request):
    """Confirmar compra - versión ultra simple"""
    from decimal import Decimal  # 👈 OBLIGATORIO
    from django.db import transaction
    
    if request.method != 'POST':
        return redirect('farmacia:registrar_compra')
    
    preview = request.session.get('previsualizacion_compra')
    if not preview:
        messages.error(request, 'No hay datos')
        return redirect('farmacia:registrar_compra')
    
    try:
        with transaction.atomic():
            compra = Compra.objects.create(
                proveedor_id=request.POST['proveedor_id'],
                numero_factura=request.POST['numero_factura'],
                fecha_factura=request.POST['fecha_factura'],
                subtotal=Decimal(str(preview['subtotal'])),
                igv=Decimal(str(preview['igv'])),
                total=Decimal(str(preview['total'])),
                observaciones=request.POST.get('observaciones', ''),
                usuario=request.user
            )
            
            for item in preview['items']:
                medicamento = Medicamento.objects.get(codigo=item['codigo'])
                
                DetalleCompra.objects.create(
                    compra=compra,
                    medicamento=medicamento,
                    cantidad=item['cantidad'],
                    precio_unitario=Decimal(str(item['precio_unitario'])),
                    lote=item['lote'],
                    fecha_vencimiento=item['fecha_vencimiento'],
                    subtotal=Decimal(str(item['subtotal']))
                )
                
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo='ENTRADA',
                    cantidad=item['cantidad'],
                    usuario=request.user,
                    referencia=f'Compra #{compra.id}',
                    precio_unitario=Decimal(str(item['precio_unitario']))
                )
            
            del request.session['previsualizacion_compra']
            messages.success(request, f'✅ Compra #{compra.id} registrada')
            return redirect('farmacia:detalle_compra', compra_id=compra.id)
            
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('farmacia:registrar_compra')
###################
@login_required
@grupo_requerido('farmacia', 'administrador')
def finalizar_compra_manual(request):
    """Toma el carrito manual y lo pasa a la previsualización de compra"""
    from datetime import datetime
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('farmacia:compra_manual')
    
    # Obtener carrito de la sesión
    carrito = request.session.get('carrito_compra')
    if not carrito or not carrito['items']:
        messages.error(request, 'No hay productos en el carrito')
        return redirect('farmacia:compra_manual')
    
    # Obtener estados del formulario
    incluye_igv = request.POST.get('incluye_igv') == 'true'
    factura_pagada = request.POST.get('factura_pagada') == 'true'
    
    # Actualizar carrito con IGV
    carrito['incluye_igv'] = incluye_igv
    if incluye_igv:
        carrito['igv'] = carrito['subtotal'] * 0.18
        carrito['total'] = carrito['subtotal'] + carrito['igv']
    else:
        carrito['igv'] = 0
        carrito['total'] = carrito['subtotal']
    
    # Guardar cambios en sesión
    request.session['carrito_compra'] = carrito
    
    # Convertir items al formato que espera previsualización
    items_preview = []
    for i, item in enumerate(carrito['items']):
        try:
            medicamento = Medicamento.objects.get(id=item['medicamento_id'])
            items_preview.append({
                'fila': i + 1,
                'codigo': item['codigo'],
                'nombre': item['nombre'],
                'cantidad': item['cantidad'],
                'lote': item['lote'],
                'fecha_vencimiento': datetime.strptime(item['fecha_vencimiento'], '%Y-%m-%d').date(),
                'precio_unitario': item['precio_unitario'],
                'subtotal': item['subtotal'],
            })
        except Medicamento.DoesNotExist:
            messages.error(request, f'Medicamento {item["nombre"]} no encontrado')
            return redirect('farmacia:compra_manual')
        except Exception as e:
            messages.error(request, f'Error con medicamento {item["nombre"]}: {str(e)}')
            return redirect('farmacia:compra_manual')
    
    # Guardar datos en sesión para la confirmación
    request.session['previsualizacion_compra'] = {
        'items': carrito['items'],
        'subtotal': float(carrito['subtotal']),
        'igv': float(carrito['igv']),
        'total': float(carrito['total']),
        'incluye_igv': carrito['incluye_igv'],
        'factura_pagada': factura_pagada
    }
    
    # Limpiar carrito manual (opcional, ya no lo necesitamos)
    # del request.session['carrito_compra']
    
    # Obtener proveedores para el template
    proveedores = Proveedor.objects.filter(activo=True).order_by('nombre')
    
    # Renderizar previsualización
    context = {
        'items': items_preview,
        'subtotal': carrito['subtotal'],
        'igv': carrito['igv'],
        'total': carrito['total'],
        'incluye_igv': carrito['incluye_igv'],
        'factura_pagada': factura_pagada,
        'proveedores': proveedores,
        'titulo': 'Previsualizar Compra'
    }
    
    return render(request, 'farmacia/compra_previsualizar.html', context)

#########################
@login_required
@grupo_requerido('farmacia', 'administrador')
def compra_individual(request):
    """Registro de compra individual (producto por producto)"""
    
    if 'carrito_compra_individual' not in request.session:
        request.session['carrito_compra_individual'] = {
            'productos': [],
            'subtotal': 0,
            'incluye_igv': False,  # Solo esto, sin igv fijo
        }
    
    context = {
        'proveedores': Proveedor.objects.filter(activo=True).order_by('nombre'),
        'carrito': request.session['carrito_compra_individual'],
        'titulo': 'Registrar Compra Individual'
    }
    return render(request, 'farmacia/compra_individual.html', context)


####################
@login_required
def buscar_medicamento_json(request):
    """Busca medicamentos por código o nombre y devuelve JSON"""
    query = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'nombre')  # 'codigo' o 'nombre'

    if not query or len(query) < (1 if tipo == 'codigo' else 2):
        return JsonResponse({'medicamentos': []})

    try:
        if tipo == 'codigo':
            filtro = Q(codigo__icontains=query)
        else:
            filtro = Q(nombre_comercial__icontains=query)

        medicamentos = Medicamento.objects.filter(
            filtro & Q(activo=True)
        ).order_by('nombre_comercial')[:20]

        data = [{
            'id': m.id,
            'codigo': m.codigo,
            'nombre': m.nombre_comercial,
            'principio_activo': m.principio_activo or '',
            'forma_farmaceutica': m.forma_farmaceutica or '',
            'fabricante': m.fabricante or '',
            'precio_venta': float(m.precio_venta),
            'stock_minimo': m.stock_minimo,
        } for m in medicamentos]

        return JsonResponse({'medicamentos': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

############################
@login_required
@grupo_requerido('farmacia', 'administrador')
def agregar_producto_compra(request):
    from decimal import Decimal
    from datetime import datetime
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        
        # Crear o buscar medicamento (igual que antes)
        if data.get('es_nuevo'):
            medicamento = Medicamento.objects.create(
                codigo=data['codigo'],
                nombre_comercial=data['nombre_comercial'],
                principio_activo=data.get('principio_activo', ''),
                forma_farmaceutica=data.get('forma_farmaceutica', ''),
                fabricante=data.get('fabricante', ''),
                precio_compra=Decimal(str(data['precio_unitario'])),
                precio_venta=Decimal(str(data.get('precio_venta', 0))),
                stock_actual=0,
                stock_minimo=int(data.get('stock_minimo', 10)),
                activo=True,
                creado_por=request.user
            )
        else:
            medicamento = get_object_or_404(Medicamento, id=data['medicamento_id'])
        
        carrito = request.session['carrito_compra_individual']
        
        nuevo_item = {
            'id': len(carrito['productos']) + 1,
            'medicamento_id': medicamento.id,
            'codigo': medicamento.codigo,
            'nombre': medicamento.nombre_comercial,
            'cantidad': int(data['cantidad']),
            'lote': data['lote'],
            'fecha_vencimiento': data['fecha_vencimiento'],
            'precio_unitario': float(data['precio_unitario']),
            'subtotal': float(data['cantidad']) * float(data['precio_unitario']),
        }
        
        carrito['productos'].append(nuevo_item)
        carrito['subtotal'] = sum(p['subtotal'] for p in carrito['productos'])
        
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'carrito': {
                'productos': carrito['productos'],
                'subtotal': carrito['subtotal'],
                'incluye_igv': carrito['incluye_igv'],
            },
            'item': nuevo_item
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

############
@login_required
@grupo_requerido('farmacia', 'administrador')
def eliminar_producto_compra(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    carrito = request.session.get('carrito_compra_individual', {'productos': []})
    
    carrito['productos'] = [p for p in carrito['productos'] if p['id'] != item_id]
    carrito['subtotal'] = sum(p['subtotal'] for p in carrito['productos'])
    
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'carrito': {
            'productos': carrito['productos'],
            'subtotal': carrito['subtotal'],
            'incluye_igv': carrito['incluye_igv'],
        }
    })

######################
@login_required
@grupo_requerido('farmacia', 'administrador')
def confirmar_compra_individual(request):
    from decimal import Decimal
    from django.db import transaction
    from django.http import JsonResponse
    from django.urls import reverse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    carrito = request.session.get('carrito_compra_individual')
    if not carrito or not carrito['productos']:
        return JsonResponse({'success': False, 'error': 'No hay productos en el carrito'})
    
    proveedor_id = request.POST.get('proveedor_id')
    numero_factura = request.POST.get('numero_factura')
    fecha_factura = request.POST.get('fecha_factura')
    factura_pagada = request.POST.get('factura_pagada') == 'on'
    incluye_igv = request.POST.get('incluye_igv') == 'on'
    
    if not proveedor_id or not numero_factura or not fecha_factura:
        return JsonResponse({'success': False, 'error': 'Complete todos los datos'})
    
    try:
        with transaction.atomic():
            subtotal = Decimal(str(carrito['subtotal']))
            
            if incluye_igv:
                igv = subtotal * Decimal('0.18')
                total = subtotal + igv
            else:
                igv = Decimal('0')
                total = subtotal
            
            observaciones = request.POST.get('observaciones', '')
            if factura_pagada:
                observaciones += ' [FACTURA PAGADA]'
            else:
                observaciones += ' [FACTURA PENDIENTE]'
            
            compra = Compra.objects.create(
                proveedor_id=proveedor_id,
                numero_factura=numero_factura,
                fecha_factura=fecha_factura,
                subtotal=subtotal,
                igv=igv,
                total=total,
                observaciones=observaciones,
                usuario=request.user
            )
            
            for item in carrito['productos']:
                medicamento = Medicamento.objects.get(id=item['medicamento_id'])
                
                DetalleCompra.objects.create(
                    compra=compra,
                    medicamento=medicamento,
                    cantidad=item['cantidad'],
                    precio_unitario=Decimal(str(item['precio_unitario'])),
                    lote=item['lote'],
                    fecha_vencimiento=item['fecha_vencimiento'],
                    subtotal=Decimal(str(item['subtotal']))
                )
                
                # ✅ REGISTRAR MOVIMIENTO DE COMPRA (AUMENTA STOCK)
                MovimientoInventario.objects.create(
                    medicamento=medicamento,
                    tipo='COMPRA',  # ✅ TIPO CORRECTO
                    cantidad=item['cantidad'],
                    usuario=request.user,
                    referencia=f'Compra #{compra.id} - {numero_factura}',
                    precio_unitario=Decimal(str(item['precio_unitario']))
                )

                # ✅ ACTUALIZAR CAMPOS DEL MEDICAMENTO
                medicamento.precio_compra = Decimal(str(item['precio_unitario']))
                medicamento.lote = item.get('lote', '')
                medicamento.fecha_vencimiento = item.get('fecha_vencimiento', None)
                medicamento.save()
            
            del request.session['carrito_compra_individual']
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('farmacia:detalle_compra', args=[compra.id])
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
########################
@login_required
@grupo_requerido('farmacia', 'administrador')
def reporte_compras(request):
    """Reporte de compras con filtros por fecha y estado de pago"""
    from datetime import datetime, timedelta
    from django.db.models import Sum, Q
    from decimal import Decimal
    
    # Valores por defecto (últimos 30 días)
    hoy = datetime.now().date()
    fecha_desde = request.GET.get('desde', (hoy - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('hasta', hoy.strftime('%Y-%m-%d'))
    estado = request.GET.get('estado', 'todas')  # 'pagadas', 'pendientes', 'todas'
    
    # Query base
    compras = Compra.objects.select_related('proveedor', 'usuario').order_by('-fecha_factura')
    
    # Filtrar por fecha
    if fecha_desde:
        compras = compras.filter(fecha_factura__gte=fecha_desde)
    if fecha_hasta:
        compras = compras.filter(fecha_factura__lte=fecha_hasta)
    
    # Filtrar por estado de pago (basado en observaciones)
    if estado == 'pagadas':
        compras = compras.filter(observaciones__icontains='[FACTURA PAGADA]')
    elif estado == 'pendientes':
        compras = compras.filter(observaciones__icontains='[FACTURA PENDIENTE]')
    
    # Calcular totales
    totales = compras.aggregate(
        total_subtotal=Sum('subtotal'),
        total_igv=Sum('igv'),
        total_general=Sum('total')
    )
    
    # Paginación
    paginator = Paginator(compras, 20)
    page = request.GET.get('page', 1)
    compras_page = paginator.get_page(page)
    
    # Preparar datos para el template
    compras_data = []
    for c in compras_page:
        # Determinar estado de pago desde observaciones
        if '[FACTURA PAGADA]' in c.observaciones:
            estado_pago = 'Pagada'
            badge_class = 'success'
        elif '[FACTURA PENDIENTE]' in c.observaciones:
            estado_pago = 'Pendiente'
            badge_class = 'danger'
        else:
            estado_pago = 'No especificado'
            badge_class = 'secondary'
        
        compras_data.append({
            'id': c.id,
            'numero_factura': c.numero_factura,
            'fecha_factura': c.fecha_factura.strftime('%d/%m/%Y'),
            'proveedor': c.proveedor.nombre,
            'ruc': c.proveedor.ruc,
            'subtotal': float(c.subtotal),
            'igv': float(c.igv),
            'total': float(c.total),
            'estado_pago': estado_pago,
            'badge_class': badge_class,
            'productos': c.detalles.count(),
            'usuario': c.usuario.username if c.usuario else 'Sistema',
            'observaciones': c.observaciones,
        })
    
    context = {
        'compras': compras_data,
        'paginator': paginator,
        'page_obj': compras_page,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
        'totales': {
            'subtotal': float(totales['total_subtotal'] or 0),
            'igv': float(totales['total_igv'] or 0),
            'total': float(totales['total_general'] or 0),
        },
        'titulo': 'Reporte de Compras'
    }
    
    return render(request, 'farmacia/reportes/compras.html', context)


####################
@login_required
@grupo_requerido('farmacia', 'administrador')
def cambiar_estado_compra(request, compra_id):
    """Cambia el estado de pago de una factura (alterna entre pagada/pendiente)"""
    compra = get_object_or_404(Compra, id=compra_id)
    
    # Determinar estado actual
    if '[FACTURA PAGADA]' in compra.observaciones:
        # Cambiar a pendiente
        nueva_obs = compra.observaciones.replace('[FACTURA PAGADA]', '[FACTURA PENDIENTE]')
        mensaje = 'Factura marcada como PENDIENTE'
        badge = 'danger'
    elif '[FACTURA PENDIENTE]' in compra.observaciones:
        # Cambiar a pagada
        nueva_obs = compra.observaciones.replace('[FACTURA PENDIENTE]', '[FACTURA PAGADA]')
        mensaje = 'Factura marcada como PAGADA'
        badge = 'success'
    else:
        # No tiene estado, agregar pendiente por defecto
        nueva_obs = compra.observaciones + ' [FACTURA PENDIENTE]'
        mensaje = 'Estado asignado: PENDIENTE'
        badge = 'danger'
    
    # Guardar cambios
    compra.observaciones = nueva_obs
    compra.save()
    
    messages.success(request, f'✅ {mensaje}')
    return redirect('farmacia:lista_compras')

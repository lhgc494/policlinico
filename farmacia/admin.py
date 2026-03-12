# farmacia/admin.py - VERSIÓN CORREGIDA (SIN ERRORES)
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Medicamento,
    Categoria,
    Presentacion,
    Proveedor,
    Venta,
    DetalleVenta,
    MovimientoInventario,
    ComboTopico,
    ComboMedicamento
)

# ==================== MEDICAMENTO (CORREGIDO) ====================
@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    # ✅ Campos que EXISTEN en el modelo simplificado
    list_display = (
        'codigo',
        'nombre_comercial',
        'principio_activo',
        'forma_farmaceutica',  # Cambiado de 'concentracion' a 'forma_farmaceutica'
        'stock_actual',
        'precio_venta',
        'activo',
        'bajo_stock_display',      # Usamos método personalizado
        'vencido_display'           # Usamos método personalizado
    )

    # ✅ Filtros corregidos (solo campos que existen)
    list_filter = (
        'activo',
        'categoria',
        'proveedor'
    )

    search_fields = (
        'codigo',
        'codigo_barras',
        'nombre_comercial',
        'principio_activo',
        'lote'
    )

    # ✅ Campos de solo lectura (propiedades que existen)
    readonly_fields = (
        'valor_inventario_display',
        'dias_vencimiento_display',
        'vencido_display',
        'proximo_vencer_display',
        'bajo_stock_display',
        'fecha_creacion',
        'fecha_actualizacion'
    )

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'codigo_barras',
                'nombre_comercial',
                'principio_activo',
            )
        }),
        ('Presentación', {
            'fields': (
                'forma_farmaceutica',
                'categoria'
            )
        }),
        ('Stock y Precios', {
            'fields': (
                'stock_actual',
                'stock_minimo',
                'precio_compra',
                'precio_venta',
                'precio_por_caja'
            )
        }),
        ('Información de Lote', {
            'fields': (
                'lote',
                'registro_sanitario',
                'fecha_vencimiento',
                'fabricante',
                'proveedor'
            )
        }),
        ('Información Comercial', {
            'fields': (
                'cantidad_por_caja',
                'activo'
            )
        }),
        ('Campos Calculados', {
            'fields': (
                'valor_inventario_display',
                'dias_vencimiento_display',
                'vencido_display',
                'proximo_vencer_display',
                'bajo_stock_display',
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'creado_por'
            ),
            'classes': ('collapse',)
        }),
    )

    # ===== MÉTODOS PERSONALIZADOS PARA MOSTRAR PROPIEDADES =====
    
    def bajo_stock_display(self, obj):
        """Muestra el estado de stock con colores"""
        if obj.bajo_stock:
            if obj.stock_actual == 0:
                return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 CRÍTICO</span>')
            return format_html('<span style="color: #ffc107; font-weight: bold;">🟡 BAJO</span>')
        return format_html('<span style="color: #28a745;">✅ OK</span>')
    bajo_stock_display.short_description = 'Stock'
    
    def vencido_display(self, obj):
        """Muestra si está vencido"""
        if obj.vencido:
            return format_html('<span style="color: #dc3545; font-weight: bold;">❌ VENCIDO</span>')
        return '✅ Vigente'
    vencido_display.short_description = 'Vencimiento'
    
    def proximo_vencer_display(self, obj):
        """Muestra si está próximo a vencer"""
        if obj.proximo_vencer:
            if obj.dias_vencimiento and obj.dias_vencimiento <= 7:
                return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 URGENTE</span>')
            return format_html('<span style="color: #ffc107; font-weight: bold;">🟡 PRONTO</span>')
        return '✅ OK'
    proximo_vencer_display.short_description = 'Próx. Vencer'
    
    def valor_inventario_display(self, obj):
        """Muestra el valor del inventario"""
        return f"S/ {obj.valor_inventario:.2f}"
    valor_inventario_display.short_description = 'Valor Inventario'
    
    def dias_vencimiento_display(self, obj):
        """Muestra los días hasta vencimiento"""
        dias = obj.dias_vencimiento
        if dias is None:
            return 'Sin fecha'
        if dias <= 7:
            return format_html('<span style="color: #dc3545;">{} días 🔴</span>', dias)
        elif dias <= 30:
            return format_html('<span style="color: #ffc107;">{} días 🟡</span>', dias)
        return f"{dias} días"
    dias_vencimiento_display.short_description = 'Días'

# ==================== CATEGORÍA ====================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'orden', 'medicamentos_count')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')
    
    def medicamentos_count(self, obj):
        return obj.medicamentos.filter(activo=True).count()
    medicamentos_count.short_description = 'Medicamentos'

# ==================== PRESENTACIÓN ====================
@admin.register(Presentacion)
class PresentacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura', 'unidad_medida', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'abreviatura')
    ordering = ('nombre',)

# ==================== PROVEEDOR ====================
@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ruc', 'tipo_proveedor', 'activo', 'fecha_registro')
    list_filter = ('tipo_proveedor', 'activo')
    search_fields = ('nombre', 'ruc', 'contacto')
    ordering = ('nombre',)

# ==================== VENTA ====================
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora', 'total', 'metodo_pago', 'usuario')
    list_filter = ('metodo_pago', 'fecha_hora')
    search_fields = ('observaciones', 'usuario__username')
    readonly_fields = ('fecha_hora', 'total', 'descuento')
    date_hierarchy = 'fecha_hora'
    ordering = ('-fecha_hora',)

# ==================== DETALLE VENTA ====================
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'medicamento', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__metodo_pago',)
    search_fields = ('medicamento__nombre_comercial', 'venta__id')
    readonly_fields = ('subtotal',)

# ==================== MOVIMIENTO INVENTARIO ====================
@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('medicamento', 'tipo', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('medicamento__nombre_comercial', 'referencia')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

# ==================== COMBOS DE TÓPICO ====================
class ComboMedicamentoInline(admin.TabularInline):
    """Para editar medicamentos dentro del combo"""
    model = ComboMedicamento
    extra = 3
    autocomplete_fields = ['medicamento']

@admin.register(ComboTopico)
class ComboTopicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_creacion', 'mostrar_precio']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    inlines = [ComboMedicamentoInline]
    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
    )

    def mostrar_precio(self, obj):
        """Muestra el precio total del combo"""
        total = obj.calcular_precio_total()
        return f"S/ {total:.2f}"
    mostrar_precio.short_description = 'Precio total'

# ==================== CONFIGURACIÓN DEL SITIO ADMIN ====================
admin.site.site_header = "Administración del Policlínico"
admin.site.site_title = "Sistema de Farmacia"
admin.site.index_title = "Panel de Administración"

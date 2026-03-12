# farmacia/admin.py - VERSIÓN ACTUALIZADA
from django.contrib import admin
from .models import (
    Medicamento, 
    Categoria, 
    Presentacion, 
    Proveedor,
    Venta,           # NUEVO: Este es el modelo correcto
    DetalleVenta,    # NUEVO: Este es el modelo correcto
    MovimientoInventario
)

# ==================== MEDICAMENTO ====================
@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    # Campos que EXISTEN en el nuevo modelo
    list_display = (
        'codigo', 
        'nombre_comercial', 
        'principio_activo', 
        'concentracion',
        'stock_actual',
        'precio_venta',
        'activo',
        'bajo_stock',      # Propiedad
        'vencido'          # Propiedad
    )
    
    list_filter = (
        'activo', 
        'requiere_receta', 
        'controlado', 
        'refrigerado',
        'categoria'
    )
    
    search_fields = (
        'codigo', 
        'nombre_comercial', 
        'nombre_generico', 
        'principio_activo',
        'lote'
    )
    
    # Campos de solo lectura (propiedades)
    readonly_fields = (
        'valor_inventario',
        'dias_vencimiento',
        'vencido',
        'proximo_vencer',
        'bajo_stock',
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo', 
                'codigo_barras',
                'nombre_comercial', 
                'nombre_generico', 
                'principio_activo', 
                'concentracion'
            )
        }),
        ('Presentación y Categoría', {
            'fields': (
                'forma_farmaceutica', 
                'presentacion', 
                'categoria'
            )
        }),
        ('Stock y Precios', {
            'fields': (
                'stock_actual', 
                'stock_minimo', 
                'stock_maximo',
                'precio_compra', 
                'precio_venta', 
                'precio_venta_mayorista'
            )
        }),
        ('Información de Lote y Proveedor', {
            'fields': (
                'lote', 
                'registro_sanitario', 
                'fecha_vencimiento',
                'fabricante', 
                'proveedor'
            )
        }),
        ('Control y Almacenamiento', {
            'fields': (
                'requiere_receta', 
                'controlado', 
                'refrigerado',
                'condiciones_almacenamiento',
                'activo'
            )
        }),
        ('Campos Automáticos', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'creado_por'
            ),
            'classes': ('collapse',)
        }),
    )

# ==================== CATEGORÍA ====================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'orden', 'medicamentos_count')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')

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

# ==================== VENTA (NUEVO) ====================
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora', 'total', 'metodo_pago', 'usuario')
    list_filter = ('metodo_pago', 'fecha_hora')
    search_fields = ('observaciones', 'usuario__username')
    readonly_fields = ('fecha_hora', 'total', 'descuento')
    date_hierarchy = 'fecha_hora'
    ordering = ('-fecha_hora',)

# ==================== DETALLE VENTA (NUEVO) ====================
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

# Configuración del admin site
admin.site.site_header = "Administración del Policlínico"
admin.site.site_title = "Sistema de Farmacia"
admin.site.index_title = "Panel de Administración"

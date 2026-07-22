# farmacia/admin.py
from django.contrib import admin
from .models import Medicamento

@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre_comercial', 'concentracion', 'stock_actual', 
                   'precio_venta', 'categoria', 'activo', 'proximo_vencer')
    list_filter = ('categoria', 'activo', 'forma_farmaceutica')
    search_fields = ('codigo', 'nombre_comercial', 'principio_activo')
    readonly_fields = ('valor_inventario', 'dias_vencimiento')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre_comercial', 'principio_activo', 'concentracion')
        }),
        ('Presentación', {
            'fields': ('forma_farmaceutica', 'presentacion', 'contenido', 'unidad_venta')
        }),
        ('Inventario', {
            'fields': ('stock_actual', 'stock_minimo', 'stock_maximo', 'ubicacion')
        }),
        ('Precios', {
            'fields': ('precio_compra', 'precio_venta', 'margen_ganancia')
        }),
        ('Control Sanitario', {
            'fields': ('laboratorio', 'registro_sanitario', 'lote', 
                      'fecha_fabricacion', 'fecha_vencimiento', 'categoria')
        }),
        ('Control', {
            'fields': ('activo', 'requiere_receta', 'observaciones')
        }),
        ('Calculados', {
            'fields': ('valor_inventario', 'dias_vencimiento'),
            'classes': ('collapse',)
        }),
    )

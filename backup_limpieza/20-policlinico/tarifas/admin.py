from django.contrib import admin
from .models import TarifaConsulta


@admin.register(TarifaConsulta)
class TarifaConsultaAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_consulta',
        'especialidad',
        'precio',
        'activo',
        'created_at'
    )

    list_filter = (
        'tipo_consulta',
        'especialidad',
        'activo'
    )

    search_fields = (
        'tipo_consulta',
        'especialidad'
    )

    ordering = ('-activo', 'tipo_consulta')

    list_editable = ('precio', 'activo')

    fieldsets = (
        ('Información de la consulta', {
            'fields': ('tipo_consulta', 'especialidad')
        }),
        ('Precio', {
            'fields': ('precio', 'activo')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


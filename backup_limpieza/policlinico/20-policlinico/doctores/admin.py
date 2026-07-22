from django.contrib import admin
from .models import Especialidad, Doctor

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_nombre_display', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    ordering = ('nombre',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni', 'especialidad_nombre', 'usuario', 'telefono', 'activo')
    list_filter = ('activo', 'especialidad',)
    search_fields = ('nombres', 'apellidos', 'dni', 'telefono', 'usuario__username')
    ordering = ('apellidos', 'nombres')
    list_per_page = 20

    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'dni', 'usuario')
        }),
        ('Información Profesional', {
            'fields': ('especialidad', 'telefono', 'email')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

    def nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
    nombre_completo.short_description = 'Nombre Completo'

    def especialidad_nombre(self, obj):
        return obj.especialidad.get_nombre_display()
    especialidad_nombre.short_description = 'Especialidad'

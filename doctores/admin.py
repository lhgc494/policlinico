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
    list_display = (
        'nombre_completo', 
        'dni', 
        'especialidades_lista',  # ✅ CAMBIADO: muestra todas las especialidades
        'usuario', 
        'telefono', 
        'activo'
    )
    list_filter = ('activo', 'especialidades')  # ✅ CAMBIADO: ahora filtra por especialidades
    search_fields = ('nombres', 'apellidos', 'dni', 'telefono', 'usuario__username')
    ordering = ('apellidos', 'nombres')
    list_per_page = 20
    
    # ✅ NUEVO: Interfaz amigable para seleccionar múltiples especialidades
    filter_horizontal = ('especialidades',)  # ¡Esto es clave!

    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'dni', 'usuario')
        }),
        ('Información Profesional', {
            'fields': ('especialidades', 'telefono', 'email'),  # ✅ CAMBIADO: especialidades (plural)
            'description': 'Puede seleccionar UNA O MÁS especialidades manteniendo CTRL o CMD'
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )

    def nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
    nombre_completo.short_description = 'Nombre Completo'

    # ✅ NUEVO: Método para mostrar todas las especialidades
    def especialidades_lista(self, obj):
        especialidades = obj.especialidades.all()
        if especialidades:
            return ", ".join([e.get_nombre_display() for e in especialidades])
        return "Sin especialidad"
    especialidades_lista.short_description = 'Especialidades'
    especialidades_lista.admin_order_field = 'especialidades__nombre'

    # ✅ OPCIONAL: Acción para asignar especialidad múltiple
    actions = ['asignar_especialidad_multiple']
    
    def asignar_especialidad_multiple(self, request, queryset):
        """Acción para asignar la misma especialidad a varios doctores"""
        from django.shortcuts import redirect
        from django.urls import reverse
        from django.http import HttpResponseRedirect
        
        # Redirige a una página intermedia (implementación simple)
        if 'asignar' in request.POST:
            especialidad_id = request.POST.get('especialidad')
            if especialidad_id:
                especialidad = Especialidad.objects.get(id=especialidad_id)
                for doctor in queryset:
                    doctor.especialidades.add(especialidad)
                self.message_user(request, f"Especialidad '{especialidad}' asignada a {queryset.count()} doctor(es)")
                return
        else:
            # Mostrar formulario simple
            from django.template.response import TemplateResponse
            opts = self.model._meta
            context = {
                'doctores': queryset,
                'especialidades': Especialidad.objects.filter(activa=True),
                'opts': opts,
                'action': 'asignar_especialidad_multiple',
            }
            return TemplateResponse(request, 'admin/doctores/asignar_especialidad.html', context)
    
    asignar_especialidad_multiple.short_description = "Asignar especialidad a seleccionados"

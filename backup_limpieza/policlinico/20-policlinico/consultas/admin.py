from django.contrib import admin
from .models import CatalogoExamen

@admin.register(CatalogoExamen)
class CatalogoExamenAdmin(admin.ModelAdmin):
    """Configuración del admin para el catálogo de exámenes"""
    
    list_display = ('nombre', 'tipo', 'precio', 'tiempo_entrega', 'activo')
    list_filter = ('tipo', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'activo')  # 'precio' ahora SÍ está en list_display
    list_per_page = 20
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'tipo', 'precio', 'activo')
        }),
        ('Detalles del Examen', {
            'fields': ('descripcion', 'tiempo_entrega', 'preparacion'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    actions = ['activar_examenes', 'desactivar_examenes']
    
    def activar_examenes(self, request, queryset):
        """Acción para activar múltiples exámenes"""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} examen(es) activado(s).')
    activar_examenes.short_description = "Activar exámenes seleccionados"
    
    def desactivar_examenes(self, request, queryset):
        """Acción para desactivar múltiples exámenes"""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} examen(es) desactivado(s).')
    desactivar_examenes.short_description = "Desactivar exámenes seleccionados"


###########################
from django.contrib import admin
from .models import CatalogoExamen, CatalogoEcografia  # Agregar CatalogoEcografia

# ... (tu código existente para CatalogoExamen)

@admin.register(CatalogoEcografia)
class CatalogoEcografiaAdmin(admin.ModelAdmin):
    """
    Panel de administración para el catálogo de ecografías
    Simple: solo nombre, precio y activo
    """
    
    list_display = ('nombre', 'precio', 'activo', 'fecha_actualizacion')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_editable = ('precio', 'activo')
    list_per_page = 20
    
    # Campos que se muestran al crear/editar
    fieldsets = (
        ('Información de la Ecografía', {
            'fields': ('nombre', 'precio', 'activo')
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    # Acciones en masa
    actions = ['activar_ecografias', 'desactivar_ecografias']
    
    def activar_ecografias(self, request, queryset):
        """Activar múltiples ecografías"""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} ecografía(s) activada(s).')
    activar_ecografias.short_description = "Activar ecografías seleccionadas"
    
    def desactivar_ecografias(self, request, queryset):
        """Desactivar múltiples ecografías"""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} ecografía(s) desactivada(s).')
    desactivar_ecografias.short_description = "Desactivar ecografías seleccionadas"
    
    # No mostrar el campo tipo en el admin (si decides no tenerlo en el modelo)
    # Si lo mantienes en el modelo pero no quieres verlo:
    exclude = []  # Si tienes campo 'tipo', agrégalo aquí: exclude = ['tipo']

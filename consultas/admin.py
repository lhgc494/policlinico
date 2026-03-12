from django.contrib import admin
from .models import CatalogoExamen, CatalogoEcografia, TopicoCatalogo, Consulta

# ============================================
# 1. CATÁLOGO DE EXÁMENES (LABORATORIO)
# ============================================
@admin.register(CatalogoExamen)
class CatalogoExamenAdmin(admin.ModelAdmin):
    """Configuración del admin para el catálogo de exámenes"""

    list_display = ('nombre', 'tipo', 'precio', 'tiempo_entrega', 'activo')
    list_filter = ('tipo', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'activo')
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
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} examen(es) activado(s).')
    activar_examenes.short_description = "Activar exámenes seleccionados"

    def desactivar_examenes(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} examen(es) desactivado(s).')
    desactivar_examenes.short_description = "Desactivar exámenes seleccionados"


# ============================================
# 2. CATÁLOGO DE ECOGRAFÍAS
# ============================================
@admin.register(CatalogoEcografia)
class CatalogoEcografiaAdmin(admin.ModelAdmin):
    """Catálogo de ecografías"""
    
    list_display = ('nombre', 'precio', 'activo')
    list_editable = ('precio', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_per_page = 20
    
    fieldsets = (
        ('Información de la Ecografía', {
            'fields': ('nombre', 'precio', 'activo')
        }),
    )
    
    actions = ['activar_ecografias', 'desactivar_ecografias']
    
    def activar_ecografias(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} ecografía(s) activada(s).')
    activar_ecografias.short_description = "Activar ecografías seleccionadas"
    
    def desactivar_ecografias(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} ecografía(s) desactivada(s).')
    desactivar_ecografias.short_description = "Desactivar ecografías seleccionadas"


# ============================================
# 3. CATÁLOGO DE TÓPICOS - CORREGIDO
# ============================================
@admin.register(TopicoCatalogo)
class TopicoCatalogoAdmin(admin.ModelAdmin):
    """Catálogo de tópicos/procedimientos"""
    
    list_display = ('nombre', 'precio', 'activo')  # 👈 SIN fecha_actualizacion
    list_editable = ('precio', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_per_page = 20
    
    fieldsets = (
        ('Información del Tópico', {
            'fields': ('nombre', 'precio', 'activo')
        }),
    )
    
    # 👈 ELIMINADO readonly_fields (no existen esos campos)
    
    actions = ['activar_topicos', 'desactivar_topicos']
    
    def activar_topicos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} tópico(s) activado(s).')
    activar_topicos.short_description = "Activar tópicos seleccionados"
    
    def desactivar_topicos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} tópico(s) desactivado(s).')
    desactivar_topicos.short_description = "Desactivar tópicos seleccionados"


# ============================================
# 4. CONSULTA
# ============================================
@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para Consultas"""
    
    list_display = ('id', 'paciente', 'tipo_consulta', 'ecografia_info', 'topico_info', 'doctor', 'estado', 'fecha', 'precio')
    list_filter = ('tipo_consulta', 'estado', 'especialidad', 'fecha')
    search_fields = ('id', 'paciente__nombres', 'paciente__apellidos', 'paciente__dni')
    list_per_page = 25
    date_hierarchy = 'fecha'
    
    def ecografia_info(self, obj):
        if obj.ecografia_catalogo:
            return f"{obj.ecografia_catalogo.nombre} - S/{obj.ecografia_catalogo.precio}"
        return "—"
    ecografia_info.short_description = "Ecografía"
    
    def topico_info(self, obj):
        if obj.topico_catalogo:
            return f"{obj.topico_catalogo.nombre} - S/{obj.topico_catalogo.precio}"
        return "—"
    topico_info.short_description = "Tópico"
    
    fieldsets = (
        ('Paciente y Tarifa', {
            'fields': ('paciente', 'tarifa')
        }),
        ('Tipo de Consulta', {
            'fields': ('tipo_consulta',)
        }),
        ('Ecografía', {
            'fields': ('ecografia_catalogo',),
            'classes': ('wide',),
            'description': 'Completar SOLO si el tipo de consulta es ECOGRAFÍA'
        }),
        ('Tópico', {
            'fields': ('topico_catalogo',),
            'classes': ('wide',),
            'description': 'Completar SOLO si el tipo de consulta es TÓPICO'
        }),
        ('Atención Médica', {
            'fields': ('especialidad', 'precio', 'doctor', 'estado')
        }),
        ('Diagnóstico y Tratamiento', {
            'fields': ('diagnostico', 'observaciones', 'tratamiento'),
            'classes': ('wide',)
        }),
        ('Fechas', {
            'fields': ('fecha', 'fecha_atencion'),
            'classes': ('collapse',)
        }),
        ('Lectura de Resultados', {
            'fields': ('es_lectura_resultados', 'descripcion_ecografia'),
            'classes': ('collapse',)
        }),
        ('Descripción del Servicio', {
            'fields': ('descripcion_servicio',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha',)

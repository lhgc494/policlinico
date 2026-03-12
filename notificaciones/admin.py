from django.contrib import admin
from .models import Notificacion

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'tipo_usuario', 'tipo', 'titulo', 'leida', 'fecha_creacion']
    list_filter = ['tipo_usuario', 'tipo', 'leida']
    search_fields = ['usuario__username', 'titulo', 'mensaje']
    list_editable = ['leida']

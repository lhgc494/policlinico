# /home/luis/policlinico/notificaciones/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('api/recientes/', views.notificaciones_recientes, name='notificaciones_recientes'),
    path('api/historial/', views.historial_notificaciones, name='historial_notificaciones'),
    path('api/marcar/<int:notificacion_id>/', views.marcar_como_leida, name='marcar_notificacion'),
    path('api/marcar-todas/', views.marcar_todas_leidas, name='marcar_todas'),
]

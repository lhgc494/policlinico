from django.urls import path
from . import views

urlpatterns = [
    path('pendientes/', views.lista_triaje_pendiente, name='lista_triaje_pendiente'),
    path('crear/<int:consulta_id>/', views.crear_triaje, name='crear_triaje'),
    path('editar/<int:triaje_id>/', views.editar_triaje, name='editar_triaje'),
    path('historial/', views.historial_triajes, name='historial_triajes'),
    path('saltar/<int:consulta_id>/', views.saltar_triaje, name='saltar_triaje'),
    ]

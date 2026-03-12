from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_paciente, name='crear_paciente'),
    path('lista/', views.lista_pacientes, name='lista_pacientes'),  # <--- nueva
    path('editar/<int:paciente_id>/', views.editar_paciente, name='editar_paciente'),
    path('editar/<int:paciente_id>/', views.editar_paciente, name='editar_paciente'),
    path('eliminar/<int:paciente_id>/', views.eliminar_paciente, name='eliminar_paciente'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]


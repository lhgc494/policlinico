from consultas.views import reportes_view, exportar_reporte_excel  
from pacientes.views import inicio  # ← Asegúrate de importar inicio
from django.contrib import admin
from django.urls import path, include 
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from pacientes.views import custom_logout
from consultas.views import reportes_view
#from pacientes.views import (
   # CustomLoginView,
  #  admin_dashboard,
  #  recepcion_dashboard,
  #  medico_dashboard,
#)

urlpatterns = [
    path('', inicio, name='inicio'),  # ← AGREGAR ESTA LÍNEA PRIMERO
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('recepcion/pacientes/', include('pacientes.urls')),  # <-- Incluye URLs de pacientes
    path('consultas/', include('consultas.urls')),
    path('pagos/', include('pagos.urls')),
    path('triaje/', include('triaje.urls')),
    path('doctor/', include('doctores.urls')),
    path('farmacia/', include('farmacia.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('reportes/', reportes_view, name='reportes'),
    path('reportes/excel/', exportar_reporte_excel, name='exportar_reporte_excel'),
    # path('login/', CustomLoginView.as_view(), name='login'),
   # path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
   # path('recepcion/', recepcion_dashboard, name='recepcion_dashboard'),
   # path('medico/', medico_dashboard, name='medico_dashboard'),
]

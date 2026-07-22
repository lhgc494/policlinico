"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from pacientes.views import inicio  # ← Asegúrate de importar inicio
from django.contrib import admin
from django.urls import path, include 
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from pacientes.views import custom_logout

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
    # path('login/', CustomLoginView.as_view(), name='login'),
   # path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
   # path('recepcion/', recepcion_dashboard, name='recepcion_dashboard'),
   # path('medico/', medico_dashboard, name='medico_dashboard'),
]

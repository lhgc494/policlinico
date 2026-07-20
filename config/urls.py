from django.conf import settings
from django.conf.urls.static import static
from consultas.views import reportes_view, exportar_reporte_excel  
from pacientes.views import inicio
from django.contrib import admin
from django.urls import path, include 
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from pacientes.views import custom_logout
from consultas.views import reportes_view


urlpatterns = [
    path('', inicio, name='inicio'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('recepcion/pacientes/', include('pacientes.urls')),
    path('consultas/', include('consultas.urls')),
    path('pagos/', include('pagos.urls')),
    path('triaje/', include('triaje.urls')),
    path('doctor/', include('doctores.urls')),
    path('farmacia/', include('farmacia.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('reportes/', reportes_view, name='reportes'),
    path('reportes/excel/', exportar_reporte_excel, name='exportar_reporte_excel'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path
from .views import detalle_orden_pago
from . import views

urlpatterns = [
    path('orden/<int:orden_id>/', detalle_orden_pago, name='detalle_orden_pago'),
    path('orden/<int:orden_id>/ticket/', views.ticket_pago, name='ticket_pago'),
    path('orden/<int:orden_id>/ticket-termico/', views.ticket_termico, name='ticket_termico'),
    ]


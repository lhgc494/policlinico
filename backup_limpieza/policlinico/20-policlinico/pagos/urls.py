from django.urls import path
from .views import detalle_orden_pago

urlpatterns = [
    path('orden/<int:orden_id>/', detalle_orden_pago, name='detalle_orden_pago'),
]


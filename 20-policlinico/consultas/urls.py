from django.urls import path
from . import views, api_views

urlpatterns = [
    # Consultas
    path('crear/<int:paciente_id>/', views.crear_consulta, name='crear_consulta'),

    # API
    path('api/doctores/', api_views.doctores_por_especialidad, name='api_doctores'),
    path('api/tarifa/<int:tarifa_id>/', api_views.tarifa_detalle, name='api_tarifa'),

    # Laboratorio - Estados de órdenes
    path('laboratorio/ordenes-pendientes/', views.lista_ordenes_pendientes, name='lista_ordenes_pendientes'),
    path('laboratorio/ordenes-en-proceso/', views.ordenes_en_proceso, name='ordenes_en_proceso'),
    path('laboratorio/ordenes-completadas/', views.ordenes_completadas, name='ordenes_completadas'),
    path('laboratorio/ordenes-entregadas/', views.ordenes_entregadas, name='ordenes_entregadas'),

    # Laboratorio - Gestión de órdenes
    path('laboratorio/mis-ordenes/', views.mis_ordenes_en_proceso, name='mis_ordenes_en_proceso'),
    path('laboratorio/orden/<int:orden_id>/', views.detalle_orden_examen, name='detalle_orden_examen'),
    path('laboratorio/orden/<int:orden_id>/asignar/', views.asignar_orden, name='asignar_orden'),
    path('laboratorio/orden/<int:orden_id>/cancelar/', views.cancelar_orden, name='cancelar_orden'),
    path('laboratorio/orden/<int:orden_id>/eliminar/', views.cancelar_eliminar_orden, name='eliminar_orden_pendiente'),

    # Laboratorio - Búsqueda
    path('laboratorio/buscar/', views.buscar_ordenes_laboratorio, name='buscar_ordenes_laboratorio'),
    path('laboratorio/buscar-global/', views.buscar_ordenes_global, name='buscar_ordenes_global'),

    # Punto de Venta Laboratorio - Carrito
    path('laboratorio/punto-venta/', views.punto_venta_laboratorio, name='punto_venta_laboratorio'),
    path('laboratorio/carrito/agregar/<int:examen_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    
    # ✅ CORREGIDO: URLs del carrito con <str:item_id>
    path('laboratorio/carrito/eliminar/<str:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('laboratorio/carrito/actualizar/<str:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    
    path('laboratorio/carrito/limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('laboratorio/cobrar-seleccionadas/', views.cobrar_ordenes_seleccionadas, name='cobrar_ordenes_seleccionadas'),

    # Procesamiento de ventas
    path('laboratorio/procesar-venta/', views.procesar_venta_ambulatoria, name='procesar_venta_ambulatoria'),
    path('laboratorio/ticket/<int:venta_id>/', views.ticket_venta_ambulatoria, name='ticket_venta_ambulatoria'),
    path('laboratorio/ticket-cobro/<int:venta_id>/', views.ticket_cobro_interno, name='ticket_cobro_interno'),
]

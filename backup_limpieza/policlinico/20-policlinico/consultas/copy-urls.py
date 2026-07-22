from django.urls import path
from . import views, api_views
from .views import (
    crear_consulta,
    lista_ordenes_pendientes,
    detalle_orden_examen,
    mis_ordenes_en_proceso,
    asignar_orden,
    cancelar_orden,
    punto_venta_laboratorio,
    agregar_al_carrito,
    eliminar_del_carrito,
    actualizar_cantidad,
    limpiar_carrito,
    procesar_venta_ambulatoria,
    ticket_venta_ambulatoria,
    ordenes_completadas,      # ¡NUEVA!
    ordenes_entregadas,       # ¡NUEVA!
    ordenes_en_proceso,  # ← ¡FALTA ESTE IMPORT!
    buscar_ordenes_laboratorio,  # ← Este también falta
    buscar_ordenes_global,  # ← Este también falta
    cancelar_eliminar_orden,  # ← Este también falta
    cobrar_ordenes_seleccionadas,  # ← Este también falta
)

urlpatterns = [
    # Consultas
    path('crear/<int:paciente_id>/', crear_consulta, name='crear_consulta'),
    
    # API
    path('api/doctores/', api_views.doctores_por_especialidad, name='api_doctores'),
    path('api/tarifa/<int:tarifa_id>/', api_views.tarifa_detalle, name='api_tarifa'),
    
    # Laboratorio - Estados de órdenes
    path('laboratorio/ordenes-pendientes/', views.lista_ordenes_pendientes, name='lista_ordenes_pendientes'),
    path('laboratorio/ordenes-completadas/', views.ordenes_completadas, name='ordenes_completadas'),      # ¡AÑADIDA!
    path('laboratorio/ordenes-entregadas/', views.ordenes_entregadas, name='ordenes_entregadas'),        # ¡AÑADIDA!
    
    # Laboratorio - Gestión de órdenes
    path('laboratorio/mis-ordenes/', views.mis_ordenes_en_proceso, name='mis_ordenes_en_proceso'),
    path('laboratorio/orden/<int:orden_id>/', views.detalle_orden_examen, name='detalle_orden_examen'),
    path('laboratorio/orden/<int:orden_id>/asignar/', views.asignar_orden, name='asignar_orden'),
    path('laboratorio/orden/<int:orden_id>/cancelar/', views.cancelar_orden, name='cancelar_orden'),
    
    # Punto de Venta Laboratorio
    path('laboratorio/punto-venta/', punto_venta_laboratorio, name='punto_venta_laboratorio'),
    path('laboratorio/carrito/agregar/<int:examen_id>/', agregar_al_carrito, name='agregar_al_carrito'),
   # path('laboratorio/carrito/eliminar/<int:examen_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
   # path('laboratorio/carrito/actualizar/<int:examen_id>/', actualizar_cantidad, name='actualizar_cantidad'),
    path('laboratorio/carrito/limpiar/', limpiar_carrito, name='limpiar_carrito'),
    path('laboratorio/procesar-venta/', views.procesar_venta_ambulatoria, name='procesar_venta_ambulatoria'),
    path('laboratorio/ticket/<int:venta_id>/', views.ticket_venta_ambulatoria, name='ticket_venta_ambulatoria'),
    path('laboratorio/ordenes-en-proceso/', views.ordenes_en_proceso, name='ordenes_en_proceso'),
    path('laboratorio/buscar/', views.buscar_ordenes_laboratorio, name='buscar_ordenes_laboratorio'),
    path('laboratorio/buscar/', views.buscar_ordenes_global, name='buscar_ordenes_global'),
   # path('laboratorio/orden/<int:orden_id>/eliminar/', views.cancelar_eliminar_orden, name='eliminar_orden_pendiente'),
   
   path('laboratorio/cobrar-seleccionadas/', views.cobrar_ordenes_seleccionadas, name='cobrar_ordenes_seleccionadas'),
    path('laboratorio/ordenes-en-proceso/', views.ordenes_en_proceso, name='ordenes_en_proceso'),  # ← ¡AGREGAR!
    path('laboratorio/ordenes-completadas/', views.ordenes_completadas, name='ordenes_completadas'),
    path('laboratorio/ordenes-entregadas/', views.ordenes_entregadas, name='ordenes_entregadas'),
    path('laboratorio/ticket-cobro/<int:venta_id>/',views.ticket_cobro_interno,name='ticket_cobro_interno'),
    path('laboratorio/carrito/eliminar/<str:item_id>/',views.eliminar_del_carrito,name='eliminar_del_carrito'),  
    path('laboratorio/orden/<int:orden_id>/eliminar/',views.cancelar_eliminar_orden, name='eliminar_orden_pendiente'),
    path('laboratorio/carrito/actualizar/<str:item_id>/', ...)
    ]


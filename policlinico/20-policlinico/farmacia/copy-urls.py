from django.urls import path
from . import views

urlpatterns = [
    path('medicamentos/', views.lista_medicamentos, name='lista_medicamentos'),
    path('medicamentos/crear/', views.crear_medicamento, name='crear_medicamento'),
    path('medicamentos/editar/<int:id>/', views.editar_medicamento, name='editar_medicamento'),
    path('medicamentos/eliminar/<int:id>/', views.eliminar_medicamento, name='eliminar_medicamento'),
    path('medicamentos/detalle/<int:id>/', views.detalle_medicamento, name='detalle_medicamento'),
    # También agregar estas URLs que faltan:
    path('medicamentos/ajustar/<int:id>/', views.ajustar_inventario, name='ajustar_inventario'),
    path('medicamentos/historial/', views.historial_movimientos, name='historial_movimientos'),

    # URLs de reportes
    path('reportes/stock-bajo/', views.reporte_stock_bajo, name='reporte_stock_bajo'),
    path('reportes/proximos-vencer/', views.reporte_proximos_vencer, name='reporte_proximos_vencer'),
    path('reportes/valor-inventario/', views.reporte_valor_inventario, name='reporte_valor_inventario'),

     # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('proveedores/detalle/<int:id>/', views.detalle_proveedor, name='detalle_proveedor'),

    path('recetas-pendientes/', views.recetas_pendientes, name='recetas_pendientes'),
    path('detalle-recetas/<int:consulta_id>/', views.detalle_recetas_consulta, name='detalle_recetas'),
    path('cancelar-recetas/<int:consulta_id>/', views.cancelar_recetas_consulta, name='cancelar_recetas'),
    # pagos
    path('procesar-pago/<int:consulta_id>/', views.procesar_pago, name='procesar_pago'),
    path('finalizar-pago/<int:consulta_id>/', views.finalizar_pago, name='finalizar_pago'),
    
    # Ventas directas (COMENTA TEMPORALMENTE HASTA QUE TENGAS LOS FORMULARIOS)
    path('ventas/', views.venta_directa, name='venta_directa'),
    path('ventas/historial/', views.historial_ventas_directas, name='historial_ventas_directas'),
    path('ventas/<int:id>/', views.detalle_venta_directa, name='detalle_venta_directa'),
    path('ventas/buscar-medicamento/', views.buscar_medicamento_venta, name='buscar_medicamento_venta'),
    ]

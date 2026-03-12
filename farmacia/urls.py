# farmacia/urls.py - VERSIÓN CORREGIDA CON app_name
from django.urls import path
from . import views

app_name = 'farmacia'  # ¡ESTO ES CLAVE!

urlpatterns = [
    # ============ INVENTARIO ============
    path('medicamentos/', views.lista_medicamentos, name='lista_medicamentos'),
    path('medicamentos/crear/', views.crear_medicamento, name='crear_medicamento'),
    path('medicamentos/editar/<int:id>/', views.editar_medicamento, name='editar_medicamento'),
    path('medicamentos/eliminar/<int:id>/', views.eliminar_medicamento, name='eliminar_medicamento'),
    path('medicamentos/detalle/<int:id>/', views.detalle_medicamento, name='detalle_medicamento'),
    path('medicamentos/ajustar/<int:id>/', views.ajustar_inventario, name='ajustar_inventario'),
    path('medicamentos/historial/', views.historial_movimientos, name='historial_movimientos'),
    
    # ============ BÚSQUEDAS AJAX ============
    path('buscar-medicamentos-ajax/', views.buscar_medicamentos_ajax, name='buscar_medicamentos_ajax'),
    path('buscar-medicamento-venta/', views.buscar_medicamento_venta, name='buscar_medicamento_venta'),

    # ============ REPORTES ============
    path('reportes/stock-bajo/', views.reporte_stock_bajo, name='reporte_stock_bajo'),
    path('reportes/proximos-vencer/', views.reporte_proximos_vencer, name='reporte_proximos_vencer'),
    path('reportes/valor-inventario/', views.reporte_valor_inventario, name='reporte_valor_inventario'),

    # ============ PROVEEDORES ============
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<int:id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('proveedores/detalle/<int:id>/', views.detalle_proveedor, name='detalle_proveedor'),

    # ============ CATEGORÍAS Y PRESENTACIONES ============
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:id>/', views.editar_categoria, name='editar_categoria'),

    path('presentaciones/', views.lista_presentaciones, name='lista_presentaciones'),
    path('presentaciones/crear/', views.crear_presentacion, name='crear_presentacion'),
    path('presentaciones/editar/<int:id>/', views.editar_presentacion, name='editar_presentacion'),

    # ============ RECETAS ============
    path('recetas-pendientes/', views.recetas_pendientes, name='recetas_pendientes'),
    path('detalle-recetas/<int:consulta_id>/', views.detalle_recetas_consulta, name='detalle_recetas_consulta'),
    path('cancelar-recetas/<int:consulta_id>/', views.cancelar_recetas_consulta, name='cancelar_recetas_consulta'),

    # ============ PAGOS ============
    path('procesar-pago/<int:consulta_id>/', views.procesar_pago, name='procesar_pago'),
    path('finalizar-pago/consulta/<int:id>/', views.finalizar_pago, {'tipo': 'consulta'}, name='finalizar_pago_consulta'),
    path('finalizar-pago/venta/<int:id>/', views.finalizar_pago, {'tipo': 'venta_directa'}, name='finalizar_pago_venta'),

    # ============ VENTAS DIRECTAS ============
    path('ventas/', views.venta_directa, name='venta_directa'),
    path('ventas/historial/', views.historial_ventas, name='historial_ventas'),
    path('ventas/<int:id>/', views.detalle_venta, name='detalle_venta'),
    path('ventas/procesar/', views.procesar_venta_directa, name='procesar_venta_directa'),
    path('ventas/actualizar-carrito/', views.actualizar_carrito, name='actualizar_carrito'),
    path('ventas/ticket/<int:id>/', views.ticket_venta, name='ticket_venta'),
    path('buscar-medicamentos-ajax/', views.buscar_medicamentos_ajax, name='buscar_medicamentos_ajax'),
    path('ventas/obtener-carrito/', views.obtener_carrito, name='obtener_carrito'),

    # ============ combos topico ==============
    path('combos/', views.lista_combos, name='lista_combos'),
    path('agregar-combo/<int:combo_id>/', views.agregar_combo_carrito, name='agregar_combo'),
    path('carrito-topico/', views.ver_carrito_topico, name='ver_carrito_topico'),
    path('eliminar-item/<str:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('obtener-carrito-topico/', views.obtener_carrito_topico, name='obtener_carrito_topico'),
    path('agregar-topico-carrito/', views.agregar_topico_carrito, name='agregar_topico_carrito'),
    path('procesar-venta-topico/', views.procesar_venta_topico, name='procesar_venta_topico'),
    path('ticket-topico/<int:venta_id>/', views.ticket_topico, name='ticket_topico'),
    # ============ COMPRAS A PROVEEDORES ============
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/registrar/', views.registrar_compra, name='registrar_compra'),
    path('compras/plantilla/', views.descargar_plantilla_compra, name='descargar_plantilla_compra'),
    path('compras/cargar-excel/', views.cargar_compra_excel, name='cargar_compra_excel'),
    path('compras/confirmar/', views.confirmar_compra, name='confirmar_compra'),
    path('compras/<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
    # ============ COMPRAS MANUALES ============
    path('compras/manual/', views.compra_manual, name='compra_manual'),
    path('compras/manual/agregar-item/', views.agregar_item_compra, name='agregar_item_compra'),
    path('compras/manual/eliminar-item/<int:item_id>/', views.eliminar_item_compra, name='eliminar_item_compra'),
    path('compras/manual/finalizar/', views.finalizar_compra_manual, name='finalizar_compra_manual'),
    #=========== compra individual========
    path('compras/individual/', views.compra_individual, name='compra_individual'),
    path('compras/individual/buscar-medicamento/', views.buscar_medicamento_json, name='buscar_medicamento_json'),
    path('compras/individual/agregar/', views.agregar_producto_compra, name='agregar_producto_compra'),
    path('compras/individual/eliminar/<int:item_id>/', views.eliminar_producto_compra, name='eliminar_producto_compra'),
    path('compras/individual/confirmar/', views.confirmar_compra_individual, name='confirmar_compra_individual'),
    #===================
    path('compras/reporte/', views.reporte_compras, name='reporte_compras'),
    path('compras/cambiar-estado/<int:compra_id>/', views.cambiar_estado_compra, name='cambiar_estado_compra'),
]

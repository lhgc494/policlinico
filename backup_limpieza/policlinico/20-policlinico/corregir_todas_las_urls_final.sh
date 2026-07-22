#!/bin/bash
cd ~/policlinico

echo "=== CORRIGIENDO TODAS LAS URLs SIN NAMESPACE EN views.py ==="

# Lista de TODAS las URLs de farmacia
URLS=(
    "editar_medicamento"
    "eliminar_medicamento"
    "detalle_medicamento"
    "ajustar_inventario"
    "lista_medicamentos"
    "crear_medicamento"
    "historial_movimientos"
    "reporte_stock_bajo"
    "reporte_proximos_vencer"
    "reporte_valor_inventario"
    "lista_proveedores"
    "crear_proveedor"
    "editar_proveedor"
    "eliminar_proveedor"
    "detalle_proveedor"
    "lista_categorias"
    "crear_categoria"
    "editar_categoria"
    "lista_presentaciones"
    "crear_presentacion"
    "editar_presentacion"
    "recetas_pendientes"
    "detalle_recetas_consulta"
    "cancelar_recetas_consulta"
    "procesar_pago"
    "finalizar_pago_consulta"
    "finalizar_pago_venta"
    "venta_directa"
    "historial_ventas"
    "detalle_venta"
    "procesar_venta_directa"
    "ticket_venta"
    "buscar_medicamentos_ajax"
    "buscar_medicamento_venta"
)

# Hacer backup
cp farmacia/views.py farmacia/views.py.before_fix

# Corregir cada URL
for url in "${URLS[@]}"; do
    echo "Corrigiendo: $url"
    
    # redirect('url' -> redirect('farmacia:url'
    sed -i "s/redirect('${url}'/redirect('farmacia:${url}'/g" farmacia/views.py
    sed -i "s/redirect(\"${url}\"/redirect(\"farmacia:${url}\"/g" farmacia/views.py
    
    # {% url 'url' -> {% url 'farmacia:url'
    sed -i "s/{% url '${url}'/{% url 'farmacia:${url}'/g" farmacia/views.py
    sed -i "s/{% url \"${url}\"/{% url \"farmacia:${url}\"/g" farmacia/views.py
done

echo ""
echo "=== VERIFICACIÓN ==="
echo "1. ¿Quedan redirect sin namespace?"
grep -n "redirect('[^']*'" farmacia/views.py | grep -v "farmacia:" | head -5 || echo "✅ Ninguno"

echo ""
echo "2. Línea 953 específicamente:"
sed -n '953p' farmacia/views.py

echo ""
echo "3. Función procesar_pago completa:"
START=$(grep -n "def procesar_pago" farmacia/views.py | cut -d: -f1)
if [ ! -z "$START" ]; then
    sed -n "${START},$((START+30))p" farmacia/views.py | grep -n "redirect\|return"
fi

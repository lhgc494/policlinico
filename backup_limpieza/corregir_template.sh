#!/bin/bash
cd ~/policlinico

echo "Corrigiendo template detalle_medicamento.html..."

# Lista de URLs a corregir
URLS=(
    "editar_medicamento"
    "eliminar_medicamento"
    "detalle_medicamento"
    "ajustar_inventario"
    "lista_medicamentos"
    "crear_medicamento"
    "historial_movimientos"
)

for url in "${URLS[@]}"; do
    echo "Corrigiendo: $url"
    # Reemplazar con comillas simples
    sed -i "s/{% url '$url'/{% url 'farmacia:$url'/g" farmacia/templates/farmacia/detalle_medicamento.html
    # Reemplazar con comillas dobles
    sed -i "s/{% url \"$url\"/{% url \"farmacia:$url\"/g" farmacia/templates/farmacia/detalle_medicamento.html
done

echo ""
echo "=== VERIFICACIÓN ==="
echo "Buscando URLs sin namespace:"
grep -n "{% url '" farmacia/templates/farmacia/detalle_medicamento.html | grep -v "farmacia:" || echo "✅ Todas corregidas"

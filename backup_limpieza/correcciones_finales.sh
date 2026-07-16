#!/bin/bash
# Correcciones finales de URLs

echo "=== APLICANDO CORRECCIONES FINALES ==="

# 1. pago_recetas.html
echo "1. Corrigiendo pago_recetas.html..."
# 'finalizar_pago' → 'finalizar_pago_consulta' (según urls.py)
sed -i "s/'finalizar_pago'/'farmacia:finalizar_pago_consulta'/g" farmacia/templates/farmacia/pago_recetas.html
# 'detalle_recetas' → 'detalle_recetas_consulta' (según urls.py)
sed -i "s/'detalle_recetas'/'farmacia:detalle_recetas_consulta'/g" farmacia/templates/farmacia/pago_recetas.html

# 2. recetas_pendientes.html
echo "2. Corrigiendo recetas_pendientes.html..."
sed -i "s/'detalle_recetas'/'farmacia:detalle_recetas_consulta'/g" farmacia/templates/farmacia/recetas_pendientes.html

# 3. Verificar otras URLs que puedan faltar
echo "3. Buscando otras URLs sin namespace..."
grep -r "{% url '" farmacia/templates/farmacia/ --include="*.html" | grep -v "farmacia:" | grep -v ".backup" || echo "✅ Todas corregidas"

echo ""
echo "=== RESUMEN DE CORRECCIONES ==="
echo "pago_recetas.html:"
grep -n "{% url" farmacia/templates/farmacia/pago_recetas.html

echo ""
echo "recetas_pendientes.html:"
grep -n "{% url" farmacia/templates/farmacia/recetas_pendientes.html

#!/bin/bash
# =============================================
# NOMBRE:      merge
# DESCRIPCIÓN: Fusiona una rama a main de forma segura
# CUÁNDO USAR: Al terminar una funcionalidad y querer incorporarla al proyecto principal
# CATEGORÍA:   Fusionar
#
# EJEMPLOS DE USO:
#   merge feature/historia-clinica
#   merge feature/modulo-pagos
# =============================================

# 1. VALIDAR QUE HAY UNA RAMA PARA FUSIONAR
if [ -z "$1" ]; then
echo "❌ Debes indicar qué rama quieres fusionar"
echo ""
echo "Uso: merge <nombre-rama>"
echo ""
echo "Ejemplos:"
echo "  merge feature/historia-clinica"
echo "  merge feature/modulo-farmacia"
echo ""
echo "📋 Ramas disponibles:"
git branch
exit 1
fi

origen="$1"
destino="main"

echo "🔄 FUSIONANDO RAMA"
echo "=================="
echo "📍 Origen:  $origen"
echo "📍 Destino: $destino"

# 2. VERIFICAR QUE LA RAMA ORIGEN EXISTE
if ! git branch | grep -q "$origen"; then
echo ""
echo "❌ La rama '$origen' no existe"
exit 1
fi

# 3. VERIFICAR QUE NO ESTAMOS EN LA MISMA RAMA
rama_actual=$(git branch --show-current)
if [ "$rama_actual" = "$origen" ]; then
echo ""
echo "⚠️  Estás en la rama '$origen'"
echo "    No puedes fusionar una rama consigo misma"
echo ""
read -p "¿Quieres cambiar a main y fusionar desde allí? (s/n): " cambiar
if [ "$cambiar" != "s" ]; then
exit 0
fi
fi

# 4. VERIFICAR CAMBIOS SIN GUARDAR
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar"
read -p "¿Quieres guardarlos antes de fusionar? (s/n): " guardar
if [ "$guardar" = "s" ]; then
read -p "Mensaje del commit: " mensaje
git add .
git commit -m "$mensaje"
echo "✅ Cambios guardados"
else
echo "⚠️  Los cambios se mantendrán sin guardar"
fi
fi

# 5. IR A MAIN Y ACTUALIZAR
echo ""
echo "📂 Cambiando a $destino..."
git checkout "$destino"
echo "✅ Estás en $destino"

echo ""
echo "⬇️  Actualizando $destino desde GitHub..."
git pull origin "$destino"
echo "✅ $destino actualizado"

# 6. FUSIONAR
echo ""
echo "🔄 Fusionando $origen en $destino..."
git merge "$origen" --no-ff -m "merge: incorporar $origen"

# 7. VERIFICAR SI HUBO CONFLICTOS
if [ $? -ne 0 ]; then
echo ""
echo "⚠️  ¡CONFLICTOS DETECTADOS!"
echo ""
echo "📋 Archivos en conflicto:"
git diff --name-only --diff-filter=U
echo ""
echo "🛠️  Opciones:"
echo "   1. Resuelve los conflictos manualmente"
echo "   2. Luego ejecuta: save \"merge: resolver conflictos\""
echo "   3. O cancela todo con: abort"
exit 1
fi

# 8. SUBIR A GITHUB
echo ""
echo "📤 Subiendo cambios a GitHub..."
git push origin "$destino"
echo "✅ Cambios subidos"

# 9. RESUMEN
echo ""
echo "=================================="
echo "✅ FUSIÓN COMPLETADA"
echo "=================================="
echo ""
echo "📍 $origen fusionado en $destino"
echo "🌐 Cambios subidos a GitHub"
echo ""
echo "💡 ¿Quieres borrar la rama '$origen'?"
echo "   Ejecuta: cleanup"
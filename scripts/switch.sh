#!/bin/bash
# =============================================
# NOMBRE:      switch
# DESCRIPCIÓN: Cambia de una rama a otra de forma segura
# CUÁNDO USAR: Cuando necesitas moverte entre ramas del proyecto
# CATEGORÍA:   Ramas
#
# EJEMPLOS DE USO:
#   switch main
#   switch develop
#   switch feature/historia-clinica
# =============================================

# 1. VALIDAR QUE HAY UN NOMBRE DE RAMA
if [ -z "$1" ]; then
echo "❌ Debes indicar a qué rama quieres cambiar"
echo ""
echo "Uso: switch <nombre-rama>"
echo ""
echo "Ejemplos:"
echo "  switch main"
echo "  switch develop"
echo "  switch feature/historia-clinica"
echo ""
echo "📋 Ramas disponibles:"
git branch -a
exit 1
fi

destino="$1"
origen=$(git branch --show-current)

echo "🔄 CAMBIANDO DE RAMA"
echo "===================="
echo "📍 De:   $origen"
echo "📍 A:    $destino"

# 2. VERIFICAR QUE LA RAMA EXISTE
if ! git branch -a | grep -q "$destino"; then
echo ""
echo "❌ La rama '$destino' no existe"
echo ""
echo "📋 Ramas disponibles:"
git branch -a
exit 1
fi

# 3. VERIFICAR CAMBIOS SIN GUARDAR
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar en '$origen'"
echo "    Si cambias de rama, estos cambios se moverán contigo"
echo ""
read -p "¿Quieres guardarlos antes de cambiar? (s/n): " guardar

if [ "$guardar" = "s" ]; then
read -p "Mensaje del commit: " mensaje
git add .
git commit -m "$mensaje"
echo "✅ Cambios guardados: $mensaje"
else
echo "⚠️  Los cambios sin guardar irán contigo a '$destino'"
fi
fi

# 4. CAMBIAR DE RAMA
echo ""
echo "🔄 Cambiando a '$destino'..."
git checkout "$destino"
echo "✅ Ahora estás en: $destino"

# 5. MOSTRAR ESTADO
echo ""
echo "📋 Últimos 3 commits en '$destino':"
echo "----------------------------------------"
git log --oneline -3

echo ""
echo "=================================="
echo "✅ CAMBIO DE RAMA COMPLETADO"
echo "=================================="
#!/bin/bash
# =============================================
# NOMBRE:      stash
# DESCRIPCIÓN: Guarda cambios temporalmente sin hacer commit
# CUÁNDO USAR: Cuando te interrumpen o necesitas cambiar de rama rápidamente
# CATEGORÍA:   Almacenar
#
# EJEMPLOS DE USO:
#   stash
#   stash "mensaje descriptivo"
# =============================================

echo "📦 GUARDADO TEMPORAL (STASH)"
echo "============================"

# 1. VERIFICAR SI HAY CAMBIOS PARA GUARDAR
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
echo "❌ No hay cambios para guardar"
echo ""
echo "📋 Estado actual del stash:"
git stash list
exit 0
fi

# 2. MOSTRAR QUÉ SE VA A GUARDAR
echo ""
echo "📋 Cambios que se guardarán:"
echo "----------------------------------------"

# Archivos modificados
modificados=$(git diff --name-only)
if [ -n "$modificados" ]; then
echo "📝 Modificados:"
echo "$modificados"
fi

# Archivos nuevos
nuevos=$(git ls-files --others --exclude-standard)
if [ -n "$nuevos" ]; then
echo "🆕 Nuevos:"
echo "$nuevos"
fi

# Archivos en staging
stageados=$(git diff --cached --name-only)
if [ -n "$stageados" ]; then
echo "📦 En staging:"
echo "$stageados"
fi

# 3. GUARDAR CON O SIN MENSAJE
echo ""
if [ -n "$1" ]; then
mensaje="$1"
git stash save "$mensaje"
echo "✅ Cambios guardados: \"$mensaje\""
else
# Mensaje automático con fecha
mensaje="WIP: $(date '+%Y-%m-%d %H:%M')"
git stash save "$mensaje"
echo "✅ Cambios guardados: \"$mensaje\""
fi

# 4. MOSTRAR LISTA DE STASHES
echo ""
echo "📋 Lista de guardados temporales:"
echo "----------------------------------------"
git stash list

# 5. INDICAR CÓMO RECUPERAR
echo ""
echo "💡 Para recuperar los cambios:"
echo "   unstash"
echo ""
echo "💡 Otros comandos útiles:"
echo "   git stash list    ← Ver todos los guardados"
echo "   git stash drop    ← Borrar último guardado"
echo "   git stash clear   ← Borrar TODOS los guardados"
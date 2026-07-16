#!/bin/bash
# =============================================
# NOMBRE:      undo
# DESCRIPCIÓN: Deshace el último commit manteniendo los cambios
# CUÁNDO USAR: Cuando hiciste commit por error o en la rama equivocada
# CATEGORÍA:   Emergencias
#
# EJEMPLOS DE USO:
#   undo
#   (No necesita argumentos, solo se ejecuta)
# =============================================

echo "⏪ DESHACIENDO ÚLTIMO COMMIT"
echo "============================"

# 1. VERIFICAR QUE HAY COMMITS
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
echo "❌ No hay commits para deshacer"
exit 1
fi

# 2. MOSTRAR EL COMMIT QUE SE VA A DESHACER
echo ""
echo "📋 Último commit:"
echo "----------------------------------------"
git log -1 --oneline
echo ""

# 3. PREGUNTAR MODO DE DESHACER
echo "¿Cómo quieres deshacer el commit?"
echo "1) Soft  ← Borra el commit pero CONSERVA los cambios (recomendado)"
echo "2) Hard  ← Borra el commit y ELIMINA los cambios (¡cuidado!)"
echo "3) Mixed ← Borra el commit y saca los cambios del staging"
read -p "Opción (1-3): " modo

# 4. EJECUTAR
echo ""
case $modo in
1)
echo "🔄 Deshaciendo (soft)..."
git reset --soft HEAD~1
echo "✅ Commit deshecho - Cambios conservados en staging"
echo ""
echo "📋 Lo que puedes hacer ahora:"
echo "   - Corregir y volver a commitear: save \"nuevo mensaje\""
echo "   - Cambiar de rama y commitear allí: switch <rama>"
;;
2)
echo "⚠️  ¡ATENCIÓN! Esto ELIMINARÁ los cambios del commit"
read -p "¿Estás completamente seguro? (ESCRIBE 'si' para confirmar): " confirmar
if [ "$confirmar" != "si" ]; then
echo "⏭️  Operación cancelada"
exit 0
fi
echo "🗑️  Deshaciendo (hard)..."
git reset --hard HEAD~1
echo "✅ Commit deshecho - Cambios ELIMINADOS"
;;
3)
echo "🔄 Deshaciendo (mixed)..."
git reset HEAD~1
echo "✅ Commit deshecho - Cambios conservados pero fuera de staging"
echo ""
echo "📋 Los cambios están en tu directorio de trabajo"
echo "   Usa 'git add' para prepararlos de nuevo"
;;
*)
echo "❌ Opción no válida. Usando soft por defecto..."
git reset --soft HEAD~1
echo "✅ Commit deshecho (soft)"
;;
esac

# 5. MOSTRAR ESTADO ACTUAL
echo ""
echo "📋 Estado actual:"
echo "----------------------------------------"
echo "📍 Rama: $(git branch --show-current)"
echo "📝 Último commit ahora:"
git log -1 --oneline
echo ""
git status -s
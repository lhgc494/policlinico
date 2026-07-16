#!/bin/bash
# =============================================
# NOMBRE:      abort
# DESCRIPCIÓN: Cancela un merge o rebase problemático y vuelve al estado anterior
# CUÁNDO USAR: Cuando un merge/rebase sale mal y quieres cancelarlo todo
# CATEGORÍA:   Emergencias
#
# EJEMPLOS DE USO:
#   abort
#   (No necesita argumentos, solo se ejecuta)
# =============================================

echo "🛑 ABORTAR OPERACIÓN"
echo "===================="

# 1. DETECTAR QUÉ OPERACIÓN ESTÁ EN CURSO
# Git guarda información de merge/rebase en .git/
hay_merge=false
hay_rebase=false
hay_cherry_pick=false

if [ -f ".git/MERGE_HEAD" ]; then
hay_merge=true
fi

if [ -d ".git/rebase-merge" ] || [ -d ".git/rebase-apply" ]; then
hay_rebase=true
fi

if [ -f ".git/CHERRY_PICK_HEAD" ]; then
hay_cherry_pick=true
fi

# 2. MOSTRAR QUÉ SE VA A CANCELAR
echo ""
echo "🔍 Detectando operación en curso..."
echo "----------------------------------------"

if $hay_merge; then
echo "⚠️  MERGE EN CURSO"
echo ""
echo "📋 Archivos en conflicto:"
git diff --name-only --diff-filter=U 2>/dev/null
operacion="merge"
elif $hay_rebase; then
echo "⚠️  REBASE EN CURSO"
echo ""
echo "📋 Estado del rebase:"
git status -s | head -5
operacion="rebase"
elif $hay_cherry_pick; then
echo "⚠️  CHERRY-PICK EN CURSO"
operacion="cherry-pick"
else
echo "✅ No hay operaciones en curso para abortar"
echo ""
echo "📋 Estado actual:"
git status -s
exit 0
fi

# 3. CONFIRMAR
echo ""
echo "⚠️  Esto CANCELARÁ el $operacion actual"
echo "    Todos los cambios del $operacion se perderán"
echo "    Volverás al estado anterior al $operacion"
echo ""
read -p "¿Estás seguro de abortar? (ESCRIBE 'abortar' para confirmar): " confirmar

if [ "$confirmar" != "abortar" ]; then
echo "⏭️  Operación cancelada"
echo "   Puedes seguir resolviendo los conflictos manualmente"
exit 0
fi

# 4. EJECUTAR ABORT
echo ""
echo "🛑 Abortando $operacion..."

case true in
$hay_merge)
git merge --abort
;;
$hay_rebase)
git rebase --abort
;;
$hay_cherry_pick)
git cherry-pick --abort
;;
esac

# 5. VERIFICAR QUE SE CANCELÓ CORRECTAMENTE
if [ $? -eq 0 ]; then
echo "✅ $operacion abortado correctamente"
else
echo "❌ Error al abortar. Intentando método alternativo..."
git reset --hard HEAD
echo "✅ Reset forzado a HEAD"
fi

# 6. MOSTRAR ESTADO FINAL
echo ""
echo "=================================="
echo "✅ OPERACIÓN ABORTADA"
echo "=================================="
echo ""
echo "📍 Has vuelto al estado anterior"
echo ""
echo "📋 Estado actual:"
echo "----------------------------------------"
echo "📍 Rama: $(git branch --show-current)"
echo "📝 Último commit:"
git log -1 --oneline
echo ""
git status -s

echo ""
echo "💡 ¿Qué puedes hacer ahora?"
echo "   - Intentar el merge de nuevo: merge <rama>"
echo "   - Pedir ayuda a un compañero"
echo "   - Revisar los cambios con: status"
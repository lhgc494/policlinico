#!/bin/bash
# =============================================
# NOMBRE:      unstash
# DESCRIPCIÓN: Recupera cambios guardados temporalmente
# CUÁNDO USAR: Después de un stash, cuando quieres retomar tu trabajo
# CATEGORÍA:   Almacenar
#
# EJEMPLOS DE USO:
#   unstash
#   unstash 1
# =============================================

echo "📤 RECUPERANDO CAMBIOS GUARDADOS"
echo "================================"

# 1. VERIFICAR QUE HAY STASHES GUARDADOS
total=$(git stash list | wc -l)

if [ "$total" -eq 0 ]; then
echo "❌ No hay cambios guardados"
echo "   Usa 'stash' para guardar cambios temporalmente"
exit 0
fi

# 2. MOSTRAR LISTA DE STASHES
echo ""
echo "📋 Cambios guardados disponibles:"
echo "----------------------------------------"
git stash list --pretty=format:"   [%gd] %s"

# 3. SELECCIONAR CUÁL RECUPERAR
echo ""
if [ "$total" -eq 1 ]; then
echo "Solo hay un stash guardado"
seleccion="0"
else
echo "Tienes $total stashes guardados"
read -p "¿Cuál quieres recuperar? (0 = más reciente, 1, 2...): " seleccion
if [ -z "$seleccion" ]; then
seleccion="0"
fi
fi

# 4. VERIFICAR CONFLICTOS POTENCIALES
echo ""
if ! git diff --quiet || ! git diff --cached --quiet; then
echo "⚠️  Tienes cambios sin guardar en este momento"
echo "    Recuperar el stash podría causar conflictos"
echo ""
read -p "¿Quieres continuar de todos modos? (s/n): " continuar
if [ "$continuar" != "s" ]; then
echo "⏭️  Operación cancelada"
echo "   Guarda tus cambios actuales primero: stash"
exit 0
fi
fi

# 5. RECUPERAR EL STASH
echo ""
echo "📤 Recuperando stash@{$seleccion}..."
git stash pop "stash@{$seleccion}"

# 6. VERIFICAR SI HUBO CONFLICTOS
if [ $? -ne 0 ]; then
echo ""
echo "⚠️  ¡CONFLICTOS AL RECUPERAR!"
echo ""
echo "📋 Archivos en conflicto:"
git diff --name-only --diff-filter=U 2>/dev/null
echo ""
echo "🛠️  Opciones:"
echo "   1. Resuelve los conflictos manualmente"
echo "   2. Los cambios del stash quedaron aplicados parcialmente"
echo "   3. Si quieres cancelar: git reset --hard HEAD"
exit 1
fi

# 7. MOSTRAR QUÉ SE RECUPERÓ
echo ""
echo "📋 Cambios recuperados:"
echo "----------------------------------------"
git status -s

# 8. MOSTRAR STASHES RESTANTES
restantes=$(git stash list | wc -l)
echo ""
echo "📦 Stashes restantes: $restantes"
if [ "$restantes" -gt 0 ]; then
git stash list --pretty=format:"   [%gd] %s"
fi

echo ""
echo "=================================="
echo "✅ CAMBIOS RECUPERADOS"
echo "=================================="
echo ""
echo "📍 Ya puedes continuar trabajando"
echo "   Cuando termines: save \"tu mensaje\""
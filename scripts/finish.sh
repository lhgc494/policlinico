#!/bin/bash
# =============================================
# NOMBRE:      finish
# DESCRIPCIÓN: Finaliza una funcionalidad: fusiona la rama actual a main y la borra
# CUÁNDO USAR: Cuando terminas por completo una funcionalidad o arreglo
# CATEGORÍA:   Fusionar
#
# EJEMPLOS DE USO:
#   finish
#   (Se ejecuta desde la rama que quieres finalizar)
# =============================================

echo "🏁 FINALIZANDO FUNCIONALIDAD"
echo "============================"

# 1. DETECTAR RAMA ACTUAL
rama_actual=$(git branch --show-current)

# Verificar que NO estamos en main o develop
if [ "$rama_actual" = "main" ] || [ "$rama_actual" = "develop" ]; then
echo "❌ Estás en '$rama_actual'"
echo "    No puedes finalizar main o develop"
echo "    Cambia a una rama de funcionalidad y vuelve a intentar"
exit 1
fi

echo "📍 Rama a finalizar: $rama_actual"

# 2. VERIFICAR CAMBIOS SIN GUARDAR
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar"
read -p "¿Quieres guardarlos antes de finalizar? (s/n): " guardar
if [ "$guardar" = "s" ]; then
read -p "Mensaje del commit: " mensaje
git add .
git commit -m "$mensaje"
echo "✅ Cambios guardados: $mensaje"
else
echo "⚠️  Los cambios sin guardar NO se incluirán"
fi
fi

# 3. VERIFICAR COMMITS SIN SUBIR
echo ""
echo "📤 Verificando commits sin subir..."
git fetch origin 2>/dev/null

# Intentar comparar con remoto, si no existe continuar
if git rev-parse --verify "origin/$rama_actual" >/dev/null 2>&1; then
sin_subir=$(git log "origin/$rama_actual"..HEAD --oneline | wc -l)
if [ "$sin_subir" -gt 0 ]; then
echo "   Tienes $sin_subir commit(s) sin subir:"
git log "origin/$rama_actual"..HEAD --oneline
echo ""
read -p "¿Subirlos ahora? (s/n): " subir
if [ "$subir" = "s" ]; then
git push origin "$rama_actual"
echo "✅ Commits subidos"
fi
else
echo "   ✅ Todo sincronizado"
fi
else
echo "   ⚠️  Rama no existe en GitHub aún"
read -p "¿Subir rama a GitHub? (s/n): " subir
if [ "$subir" = "s" ]; then
git push -u origin "$rama_actual"
echo "✅ Rama subida"
fi
fi

# 4. IR A MAIN Y ACTUALIZAR
echo ""
echo "📂 Cambiando a main..."
git checkout main
echo "✅ Estás en main"

echo ""
echo "⬇️  Actualizando main desde GitHub..."
git pull origin main
echo "✅ Main actualizado"

# 5. FUSIONAR LA RAMA
echo ""
echo "🔄 Fusionando $rama_actual en main..."
git merge "$rama_actual" --no-ff -m "merge: incorporar $rama_actual"

# 6. VERIFICAR SI HUBO CONFLICTOS
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

# 7. SUBIR A GITHUB
echo ""
echo "📤 Subiendo cambios a GitHub..."
git push origin main
echo "✅ Cambios subidos"

# 8. BORRAR RAMA LOCAL
echo ""
read -p "🗑️  ¿Borrar rama local '$rama_actual'? (s/n): " borrar_local
if [ "$borrar_local" = "s" ]; then
git branch -d "$rama_actual" 2>/dev/null
if [ $? -eq 0 ]; then
echo "✅ Rama local borrada: $rama_actual"
else
echo "⚠️  No se pudo borrar, forzando..."
git branch -D "$rama_actual"
echo "✅ Rama local borrada (forzado): $rama_actual"
fi
else
echo "⏭️  Rama local conservada"
fi

# 9. BORRAR RAMA REMOTA
echo ""
read -p "🌐 ¿Borrar rama remota 'origin/$rama_actual' en GitHub? (s/n): " borrar_remoto
if [ "$borrar_remoto" = "s" ]; then
git push origin --delete "$rama_actual" 2>/dev/null
if [ $? -eq 0 ]; then
echo "✅ Rama remota borrada: $rama_actual"
else
echo "⚠️  No se encontró la rama en GitHub"
fi
fi

# 10. RESUMEN FINAL
echo ""
echo "=================================="
echo "✅ FUNCIONALIDAD FINALIZADA"
echo "=================================="
echo ""
echo "📍 Fusionado: $rama_actual → main"
echo "🌐 Cambios en GitHub"
echo "📍 Ahora estás en: main"
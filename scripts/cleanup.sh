#!/bin/bash
# =============================================
# NOMBRE:      cleanup
# DESCRIPCIÓN: Limpia ramas locales que ya fueron fusionadas
# CUÁNDO USAR: Después de varios features terminados, o al final de la semana
# CATEGORÍA:   Ramas
# =============================================

echo "🧹 LIMPIEZA DE RAMAS"
echo "===================="

# 1. ACTUALIZAR REFERENCIAS
echo ""
echo "📥 Actualizando referencias remotas..."
git fetch --prune
echo "✅ Referencias actualizadas"

# 2. MOSTRAR RAMAS LOCALES
echo ""
echo "📋 RAMAS LOCALES:"
echo "----------------------------------------"
git branch

# 3. IDENTIFICAR RAMAS FUSIONADAS
echo ""
echo "🔍 Buscando ramas que ya fueron fusionadas a main..."
echo "   (Se excluyen main y develop por seguridad)"
echo ""

ramas_mergeadas=$(git branch --merged main | grep -v "\*\|main\|develop" | sed 's/^[ \t]*//')

if [ -z "$ramas_mergeadas" ]; then
  echo "✅ No hay ramas para limpiar. ¡Todo en orden!"
  exit 0
fi

echo "📋 RAMAS FUSIONADAS (seguras para borrar):"
echo "----------------------------------------"
echo "$ramas_mergeadas"
echo ""

# 4. PREGUNTAR POR CADA RAMA (corregido)
echo "¿Qué ramas quieres borrar?"
echo ""

while IFS= read -r rama; do
  if [ -n "$rama" ]; then
    echo -n "🗑️  ¿Borrar '$rama'? (s/n): "
    read -r respuesta </dev/tty
    if [ "$respuesta" = "s" ]; then
      git branch -d "$rama" 2>/dev/null
      if [ $? -eq 0 ]; then
        echo "   ✅ Borrada: $rama"
      else
        git branch -D "$rama"
        echo "   ✅ Borrada (forzado): $rama"
      fi
    else
      echo "   ⏭️  Conservada: $rama"
    fi
    echo ""
  fi
done <<< "$ramas_mergeadas"

# 5. PREGUNTAR POR RAMAS REMOTAS
echo -n "🌐 ¿Quieres borrar también las ramas remotas en GitHub? (s/n): "
read -r borrar_remoto </dev/tty

if [ "$borrar_remoto" = "s" ]; then
  while IFS= read -r rama; do
    if [ -n "$rama" ]; then
      echo -n "🗑️  ¿Borrar '$rama' en GitHub? (s/n): "
      read -r respuesta_remoto </dev/tty
      if [ "$respuesta_remoto" = "s" ]; then
        git push origin --delete "$rama" 2>/dev/null
        if [ $? -eq 0 ]; then
          echo "   ✅ Borrada en GitHub: $rama"
        else
          echo "   ⚠️  No se encontró '$rama' en GitHub"
        fi
      fi
    fi
  done <<< "$ramas_mergeadas"
fi

# 6. RESUMEN FINAL
echo ""
echo "=================================="
echo "✅ LIMPIEZA COMPLETADA"
echo "=================================="
echo ""
echo "📋 Ramas actuales:"
git branch

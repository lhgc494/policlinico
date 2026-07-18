cat > ~/policlinico/scripts/merge.sh << 'EOF'
#!/bin/bash
# =============================================
# NOMBRE:      merge
# DESCRIPCIÓN: Fusiona una rama a otra (por defecto main)
# CUÁNDO USAR: Al terminar una funcionalidad y querer incorporarla
# CATEGORÍA:   Fusionar
#
# EJEMPLOS DE USO:
#   merge feature/historia-clinica
#   merge feature/historia-clinica develop
# =============================================

if [ -z "$1" ]; then
  echo "❌ Debes indicar qué rama quieres fusionar"
  echo ""
  echo "Uso: merge <origen> [destino]"
  echo ""
  echo "Ejemplos:"
  echo "  merge feature/historia-clinica           → fusiona a main"
  echo "  merge feature/historia-clinica develop   → fusiona a develop"
  exit 1
fi

origen="$1"
destino="${2:-main}"

echo "🔄 FUSIONANDO RAMA"
echo "=================="
echo "📍 Origen:  $origen"
echo "📍 Destino: $destino"

# Verificar que la rama origen existe
if ! git branch | grep -q "$origen"; then
  echo "❌ La rama '$origen' no existe"
  exit 1
fi

# Verificar que no estamos en la misma rama
rama_actual=$(git branch --show-current)
if [ "$rama_actual" = "$origen" ]; then
  echo "⚠️  Estás en la rama '$origen'. Cambiando a $destino..."
  git checkout "$destino"
fi

# Verificar cambios sin guardar
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "⚠️  Tienes cambios sin guardar"
  read -p "¿Guardarlos antes de fusionar? (s/n): " guardar </dev/tty
  if [ "$guardar" = "s" ]; then
    read -p "Mensaje del commit: " mensaje </dev/tty
    git add .
    git commit -m "$mensaje"
    echo "✅ Cambios guardados"
  fi
fi

# Ir a destino y actualizar
echo ""
echo "📂 Cambiando a $destino..."
git checkout "$destino"
echo "✅ Estás en $destino"

echo ""
echo "⬇️  Actualizando $destino desde GitHub..."
git pull origin "$destino" 2>/dev/null || echo "⚠️  No se pudo actualizar desde GitHub"
echo "✅ $destino actualizado"

# Fusionar
echo ""
echo "🔄 Fusionando $origen en $destino..."
git merge "$origen" --no-ff -m "merge: incorporar $origen en $destino"

if [ $? -ne 0 ]; then
  echo ""
  echo "⚠️  ¡CONFLICTOS DETECTADOS!"
  echo "📋 Archivos en conflicto:"
  git diff --name-only --diff-filter=U
  echo "  Opciones:"
  echo "    1. Resuelve los conflictos manualmente"
  echo "    2. Ejecuta: save \"merge: resolver conflictos\""
  echo "    3. Cancela: abort"
  exit 1
fi

# Subir a GitHub
echo ""
echo "📤 Subiendo cambios a GitHub..."
git push origin "$destino"
echo "✅ Cambios subidos"

# Resumen
echo ""
echo "=================================="
echo "✅ FUSIÓN COMPLETADA"
echo "=================================="
echo "📍 $origen fusionado en $destino"
echo "🌐 Cambios subidos a GitHub"
echo ""
echo "💡 ¿Quieres borrar la rama '$origen'?"
echo "   Ejecuta: cleanup"
EOF

chmod +x ~/policlinico/scripts/merge.sh
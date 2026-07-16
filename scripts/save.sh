#!/bin/bash
# =============================================
# NOMBRE:      save
# DESCRIPCIÓN: Guarda cambios en local y los sube a GitHub
# CUÁNDO USAR: Cada 15-30 minutos durante el trabajo diario
# CATEGORÍA:   Diario
# EJEMPLO USO:   save "feat: añadir módulo de farmacia"

# =============================================

# 1. VALIDAR QUE HAY UN MENSAJE
# Sin mensaje no hay commit. Obliga a documentar qué hiciste
if [ -z "$1" ]; then
echo "❌ Debes escribir un mensaje de commit"
echo ""
echo "Uso: save \"tipo: descripción de lo que hiciste\""
echo ""
echo "Ejemplos:"
echo "  save \"feat: añadir búsqueda de pacientes\""
echo "  save \"fix: corregir error en cálculo de tarifas\""
echo "  save \"docs: actualizar instrucciones de instalación\""
echo "  save \"refactor: simplificar lógica de horarios\""
exit 1
fi

# 2. DETECTAR RAMA ACTUAL
# Guarda en qué rama estás para usarla después
rama=$(git branch --show-current)
echo "📍 Rama actual: $rama"

# 3. VER SI HAY CAMBIOS
# Si no hay nada que guardar, avisa y sale
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
echo "⚠️  No hay cambios para guardar"
exit 0
fi

# 4. AÑADIR TODO
# Pasa todos los cambios al staging area
echo "📦 Preparando cambios..."
git add .
echo "✅ Archivos preparados"

# 5. HACER COMMIT
# Guarda el snapshot en el historial con el mensaje proporcionado
echo "💾 Guardando cambios..."
git commit -m "$1"
echo "✅ Commit creado: $1"

# 6. SUBIR A GITHUB
# Sincroniza con el repositorio remoto
echo "📤 Subiendo a GitHub..."
git push origin "$rama"
echo "✅ Cambios en GitHub"

# 7. RESUMEN
echo ""
echo "=================================="
echo "✅ GUARDADO COMPLETO"
echo "=================================="
echo "📝 Mensaje: $1"
echo "📍 Rama:    $rama"
echo "🌐 GitHub:  Actualizado"
#!/bin/bash
# =============================================
# NOMBRE:      status
# DESCRIPCIÓN: Muestra un resumen rápido del estado del proyecto
# CUÁNDO USAR: Al iniciar el día, antes de guardar cambios, o cuando necesitas orientarte
# CATEGORÍA:   Diario
# EJEMPLO DE USO: status
# =============================================

# 1. RAMA ACTUAL
rama=$(git branch --show-current)
echo "📍 RAMA ACTUAL: $rama"

# 2. ESTADO DE ARCHIVOS
echo ""
echo "📂 ARCHIVOS:"
echo "----------------------------------------"

# Contar archivos modificados, nuevos y eliminados
modificados=$(git diff --name-only | wc -l)
stageados=$(git diff --cached --name-only | wc -l)
nuevos=$(git ls-files --others --exclude-standard | wc -l)

echo "   Modificados sin guardar: $modificados"
echo "   En staging (listos):     $stageados"
echo "   Archivos nuevos:          $nuevos"

# 3. COMMITS SIN SUBIR
echo ""
echo "📤 COMMITS SIN SUBIR A GITHUB:"
echo "----------------------------------------"

# Ver commits locales que no están en GitHub
git fetch origin 2>/dev/null
sin_subir=$(git log origin/"$rama"..HEAD --oneline 2>/dev/null | wc -l)

if [ "$sin_subir" -gt 0 ]; then
echo "   Tienes $sin_subir commit(s) sin subir:"
git log origin/"$rama"..HEAD --oneline 2>/dev/null
else
echo "   ✅ Todo sincronizado con GitHub"
fi

# 4. ÚLTIMOS COMMITS
echo ""
echo "📋 ÚLTIMOS 5 COMMITS:"
echo "----------------------------------------"
git log --oneline -5

# 5. ARCHIVOS MODIFICADOS (DETALLE)
echo ""
echo "📝 ARCHIVOS MODIFICADOS:"
echo "----------------------------------------"
if [ "$modificados" -gt 0 ]; then
git diff --name-only
else
echo "   Ninguno"
fi

# 6. ARCHIVOS NUEVOS (DETALLE)
echo ""
echo "🆕 ARCHIVOS NUEVOS (sin seguimiento):"
echo "----------------------------------------"
if [ "$nuevos" -gt 0 ]; then
git ls-files --others --exclude-standard
else
echo "   Ninguno"
fi

echo ""
echo "=================================="
echo "✅ Estado del proyecto mostrado"
echo "=================================="
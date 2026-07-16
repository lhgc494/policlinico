#!/bin/bash
# =============================================
# NOMBRE:      update
# DESCRIPCIÓN: Trae los últimos cambios desde GitHub
# CUÁNDO USAR: Al iniciar el día, antes de empezar nueva funcionalidad
# CATEGORÍA:   Diario
#
# EJEMPLOS DE USO:
#   update
#   (No necesita argumentos, solo se ejecuta)
# =============================================

echo "⬇️  ACTUALIZANDO PROYECTO DESDE GITHUB"
echo "=================================="

# 1. DETECTAR RAMA ACTUAL
rama=$(git branch --show-current)
echo "📍 Rama actual: $rama"

# 2. GUARDAR CAMBIOS LOCALES (SI LOS HAY)
# Si hay cambios sin guardar, pregunta si quiere guardarlos
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar"
read -p "¿Quieres guardarlos antes de actualizar? (s/n): " guardar
if [ "$guardar" = "s" ]; then
read -p "Mensaje del commit: " mensaje
git add .
git commit -m "$mensaje"
echo "✅ Cambios guardados"
fi
fi

# 3. TRAER CAMBIOS DE GITHUB
echo ""
echo "📥 Descargando cambios..."
git pull origin "$rama"
echo "✅ Proyecto actualizado"

# 4. RESUMEN DE LO NUEVO
echo ""
echo "📋 ÚLTIMOS CAMBIOS RECIBIDOS:"
echo "----------------------------------------"
git log --oneline -3

# 5. VERIFICAR DEPENDENCIAS (PROYECTOS PYTHON/NODE)
echo ""
echo "🔍 Verificando dependencias..."

if [ -f "requirements.txt" ]; then
read -p "¿Actualizar dependencias Python? (s/n): " deps
if [ "$deps" = "s" ]; then
pip install -r requirements.txt
echo "✅ Dependencias Python actualizadas"
fi
elif [ -f "package.json" ]; then
read -p "¿Actualizar dependencias Node? (s/n): " deps
if [ "$deps" = "s" ]; then
npm install
echo "✅ Dependencias Node actualizadas"
fi
fi

echo ""
echo "=================================="
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "=================================="
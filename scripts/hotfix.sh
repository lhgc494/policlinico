#!/bin/bash
# =============================================
# NOMBRE:      hotfix
# DESCRIPCIÓN: Crea una rama de emergencia para arreglar un bug en producción
# CUÁNDO USAR: Cuando hay un bug crítico que debe arreglarse YA
# CATEGORÍA:   Versionado
#
# EJEMPLOS DE USO:
#   hotfix error-pagos
#   hotfix caida-servidor
# =============================================

echo "🚨 CREANDO HOTFIX DE EMERGENCIA"
echo "================================"

# 1. VALIDAR QUE HAY UN NOMBRE
if [ -z "$1" ]; then
echo "❌ Debes describir el problema a arreglar"
echo ""
echo "Uso: hotfix <descripción-del-bug>"
echo ""
echo "Ejemplos:"
echo "  hotfix error-calculo-pagos"
echo "  hotfix caida-servidor"
echo "  hotfix paciente-no-se-registra"
exit 1
fi

nombre="$1"
rama="hotfix/$nombre"

echo "🚨 Problema: $nombre"
echo "📍 Rama:     $rama"

# 2. VERIFICAR CAMBIOS SIN GUARDAR
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar"
read -p "¿Guardarlos con stash antes de continuar? (s/n): " guardar
if [ "$guardar" = "s" ]; then
git stash save "WIP antes de hotfix: $nombre"
echo "✅ Cambios guardados con stash"
fi
fi

# 3. IR A MAIN Y ACTUALIZAR
echo ""
echo "📂 Cambiando a main..."
git checkout main
echo "✅ Estás en main"

echo ""
echo "⬇️  Actualizando desde GitHub..."
git pull origin main
echo "✅ Main actualizado"

# 4. CREAR RAMA HOTFIX DESDE MAIN
echo ""
echo "🚨 Creando rama de emergencia: $rama"
git checkout -b "$rama"
echo "✅ Rama creada"

# 5. INSTRUCCIONES
echo ""
echo "=================================="
echo "✅ HOTFIX INICIADO"
echo "=================================="
echo ""
echo "📍 Rama actual: $rama"
echo ""
echo "📋 Flujo de trabajo:"
echo "   1. Arregla el bug"
echo "   2. Guarda cambios:  save \"fix: descripción\""
echo "   3. Cuando termines:  finish"
echo ""
echo "⚠️  RECUERDA:"
echo "   - Trabaja RÁPIDO, es una emergencia"
echo "   - Prueba bien el arreglo"
echo "   - Haz finish para llevar el arreglo a main"
echo "   - Luego crea una nueva release si es necesario"
echo ""
echo "💡 Después del hotfix:"
echo "   - Crea release: release 1.0.1 \"Hotfix: $nombre\""
echo "   - Despliega: deploy"
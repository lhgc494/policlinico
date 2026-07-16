#!/bin/bash
# =============================================
# NOMBRE:      feature
# DESCRIPCIÓN: Crea una nueva rama para desarrollar una funcionalidad
# CUÁNDO USAR: Al empezar una nueva característica del proyecto
# CATEGORÍA:   Ramas
#
# EJEMPLOS DE USO:
#   feature historia-clinica
#   feature modulo-pagos
#   feature buscar-pacientes
# =============================================

# 1. VALIDAR QUE HAY UN NOMBRE
if [ -z "$1" ]; then
echo "❌ Debes poner un nombre a la funcionalidad"
echo ""
echo "Uso: feature <nombre-funcionalidad>"
echo ""
echo "Ejemplos:"
echo "  feature historia-clinica"
echo "  feature modulo-farmacia"
echo "  feature buscar-pacientes"
echo "  feature arreglar-bug-pagos"
exit 1
fi

nombre="$1"
rama="feature/$nombre"

echo "🌿 CREANDO NUEVA FUNCIONALIDAD"
echo "=============================="
echo "📍 Nombre: $nombre"
echo "📍 Rama:   $rama"

# 2. IR A MAIN
echo ""
echo "📂 Cambiando a rama principal..."
git checkout main
echo "✅ Estás en main"

# 3. ACTUALIZAR MAIN
echo ""
echo "⬇️  Actualizando desde GitHub..."
git pull origin main
echo "✅ Rama main actualizada"

# 4. CREAR RAMA
echo ""
echo "🌿 Creando rama $rama..."
git checkout -b "$rama"
echo "✅ Rama creada"

# 5. CONFIRMAR
echo ""
echo "=================================="
echo "✅ FUNCIONALIDAD INICIADA"
echo "=================================="
echo ""
echo "📍 Rama actual: $rama"
echo ""
echo "📋 Flujo de trabajo:"
echo "   1. Desarrolla tu código"
echo "   2. Guarda cambios:  save \"feat: descripción\""
echo "   3. Cuando termines:  finish"
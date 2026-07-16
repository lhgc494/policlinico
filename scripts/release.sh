#!/bin/bash
# =============================================
# NOMBRE:      release
# DESCRIPCIÓN: Crea una nueva versión etiquetada del proyecto
# CUÁNDO USAR: Al finalizar un conjunto de funcionalidades o preparar despliegue
# CATEGORÍA:   Versionado
#
# EJEMPLOS DE USO:
#   release 1.0.0 "Primera versión estable"
#   release 1.1.0 "Añadido módulo de farmacia"
#   release 2.0.0
# =============================================

echo "🏷️  CREANDO NUEVA VERSIÓN"
echo "========================="

# 1. VALIDAR QUE ESTAMOS EN MAIN
rama=$(git branch --show-current)
if [ "$rama" != "main" ]; then
echo "⚠️  No estás en la rama main (estás en '$rama')"
echo "    Las releases deben crearse desde main"
echo ""
read -p "¿Quieres cambiar a main? (s/n): " cambiar
if [ "$cambiar" = "s" ]; then
git checkout main
echo "✅ Cambiado a main"
else
echo "❌ La release debe crearse desde main. Cancelado."
exit 1
fi
fi

# 2. ACTUALIZAR MAIN
echo ""
echo "⬇️  Actualizando main desde GitHub..."
git pull origin main
echo "✅ Main actualizado"

# 3. PEDIR VERSIÓN
echo ""
if [ -z "$1" ]; then
read -p "Número de versión (ej: 1.0.0): " version
else
version="$1"
fi

# Validar formato de versión
if ! echo "$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
echo "⚠️  El formato recomendado es X.Y.Z (ej: 1.0.0)"
read -p "¿Continuar con '$version'? (s/n): " continuar
if [ "$continuar" != "s" ]; then
exit 0
fi
fi

# 4. PEDIR DESCRIPCIÓN
echo ""
if [ -z "$2" ]; then
read -p "Descripción de la versión: " descripcion
else
descripcion="$2"
fi

# 5. MOSTRAR QUÉ SE INCLUYE EN LA VERSIÓN
echo ""
echo "📋 Cambios incluidos en v$version:"
echo "----------------------------------------"

# Buscar último tag
ultimo_tag=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -n "$ultimo_tag" ]; then
echo "   Desde $ultimo_tag hasta ahora:"
git log --oneline "$ultimo_tag"..HEAD
total=$(git log --oneline "$ultimo_tag"..HEAD | wc -l)
else
echo "   (Primera versión del proyecto)"
git log --oneline
total=$(git log --oneline | wc -l)
fi

echo ""
echo "📊 Total commits: $total"

# 6. CONFIRMAR
echo ""
echo "🏷️  Tag a crear: v$version"
echo "📝 Descripción: $descripcion"
echo "📊 Commits incluidos: $total"
echo ""
read -p "¿Crear esta versión? (s/n): " confirmar

if [ "$confirmar" != "s" ]; then
echo "⏭️  Release cancelada"
exit 0
fi

# 7. CREAR TAG
echo ""
echo "🏷️  Creando tag v$version..."

if [ -n "$descripcion" ]; then
git tag -a "v$version" -m "$descripcion"
else
git tag -a "v$version" -m "Versión $version"
fi

echo "✅ Tag v$version creado localmente"

# 8. SUBIR TAG A GITHUB
echo ""
echo "📤 Subiendo tag a GitHub..."
git push origin "v$version"
echo "✅ Tag subido a GitHub"

# 9. RESUMEN
echo ""
echo "=================================="
echo "✅ VERSIÓN v$version CREADA"
echo "=================================="
echo ""
echo "📋 Resumen:"
echo "   Versión:    v$version"
echo "   Descripción: $descripcion"
echo "   Commits:    $total"
echo "   En GitHub:  ✅"
echo ""
echo "💡 Próximos pasos:"
echo "   - Desplegar: deploy"
echo "   - Ver versiones: versions"
echo "   - Crear hotfix: hotfix"
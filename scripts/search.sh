#!/bin/bash
# =============================================
# NOMBRE:      search
# DESCRIPCIÓN: Busca commits por mensaje, archivo o contenido
# CUÁNDO USAR: Cuando necesitas encontrar un cambio específico en el historial
# CATEGORÍA:   Investigar
#
# EJEMPLOS DE USO:
#   search "historia clinica"
#   search "bug" --archivo pacientes/models.py
# =============================================

echo "🔍 BUSCAR EN EL HISTORIAL"
echo "========================="

# 1. MENÚ DE BÚSQUEDA
echo ""
echo "¿Qué quieres buscar?"
echo "1) Palabra en mensajes de commit"
echo "2) Commits que modificaron un archivo específico"
echo "3) Commits que añadieron o eliminaron una palabra en el código"
echo "4) Commits de un rango de fechas"
read -p "Opción (1-4): " tipo

echo ""
echo "----------------------------------------"

case $tipo in
1)
# Buscar en mensajes de commit
read -p "Palabra a buscar en mensajes: " palabra
echo ""
echo "📋 Commits que contienen '$palabra' en el mensaje:"
echo "----------------------------------------"

resultado=$(git log --oneline --grep="$palabra" -i)

if [ -z "$resultado" ]; then
echo "❌ No se encontraron commits con '$palabra'"
else
echo "$resultado"
total=$(echo "$resultado" | wc -l)
echo ""
echo "📊 Total: $total commits"

read -p "¿Ver detalle de algún commit? (hash o Enter para saltar): " hash
if [ -n "$hash" ]; then
echo ""
git show "$hash" --stat
fi
fi
;;

2)
# Buscar commits que tocaron un archivo
read -p "Nombre del archivo: " archivo

# Verificar si existe actualmente o en historial
if [ ! -f "$archivo" ] && [ -z "$(git log --oneline -- "$archivo" 2>/dev/null)" ]; then
echo ""
echo "❌ El archivo '$archivo' no existe ni en el historial"
echo ""
echo "💡 Sugerencia: busca con 'find . -name \"*nombre*\"'"
exit 1
fi

echo ""
echo "📋 Commits que modificaron '$archivo':"
echo "----------------------------------------"

resultado=$(git log --oneline -- "$archivo")

echo "$resultado"
total=$(echo "$resultado" | wc -l)
echo ""
echo "📊 Total: $total commits"

read -p "¿Ver cambios de algún commit? (hash o Enter para saltar): " hash
if [ -n "$hash" ]; then
echo ""
git show "$hash" -- "$archivo"
fi
;;

3)
# Buscar en el contenido (pickaxe)
read -p "Palabra o código a buscar: " palabra
echo ""
echo "🔍 Buscando '$palabra' en el historial de cambios..."
echo "   (Esto puede tardar un poco)"
echo ""
echo "📋 Commits que añadieron o eliminaron '$palabra':"
echo "----------------------------------------"

resultado=$(git log --oneline -S"$palabra")

if [ -z "$resultado" ]; then
echo "❌ No se encontraron cambios con '$palabra'"
else
echo "$resultado"
total=$(echo "$resultado" | wc -l)
echo ""
echo "📊 Total: $total commits"

read -p "¿Ver detalle de algún commit? (hash o Enter para saltar): " hash
if [ -n "$hash" ]; then
echo ""
git show "$hash" --stat
fi
fi
;;

4)
# Buscar por rango de fechas
echo "📅 Búsqueda por fechas"
echo ""
read -p "Desde (YYYY-MM-DD): " desde
read -p "Hasta (YYYY-MM-DD, Enter para hoy): " hasta

if [ -z "$desde" ]; then
echo "❌ Debes indicar al menos la fecha de inicio"
exit 1
fi

if [ -z "$hasta" ]; then
hasta=$(date '+%Y-%m-%d')
fi

echo ""
echo "📋 Commits entre $desde y $hasta:"
echo "----------------------------------------"

resultado=$(git log --oneline --after="$desde" --before="$hasta 23:59:59")

if [ -z "$resultado" ]; then
echo "❌ No se encontraron commits en ese rango"
else
echo "$resultado"
total=$(echo "$resultado" | wc -l)
echo ""
echo "📊 Total: $total commits"
fi
;;

*)
echo "❌ Opción no válida"
exit 1
;;
esac

echo ""
echo "=================================="
echo "✅ BÚSQUEDA COMPLETADA"
echo "=================================="
#!/bin/bash
# =============================================
# NOMBRE:      blame
# DESCRIPCIÓN: Muestra quién modificó cada línea de un archivo y cuándo
# CUÁNDO USAR: Cuando necesitas saber quién escribió un código o cuándo se modificó
# CATEGORÍA:   Investigar
#
# EJEMPLOS DE USO:
#   blame pacientes/models.py
#   blame consultas/views.py 50
# =============================================

echo "👤 INVESTIGANDO CAMBIOS POR LÍNEA"
echo "=================================="

# 1. VALIDAR QUE HAY UN ARCHIVO
if [ -z "$1" ]; then
echo "❌ Debes indicar qué archivo investigar"
echo ""
echo "Uso: blame <archivo> [número de líneas]"
echo ""
echo "Ejemplos:"
echo "  blame pacientes/models.py"
echo "  blame consultas/views.py 20"
echo ""
echo "📋 Archivos modificados recientemente:"
git diff --name-only HEAD~5 2>/dev/null | head -10
exit 1
fi

archivo="$1"
lineas="${2:-30}"  # Por defecto 30 líneas

# 2. VERIFICAR QUE EL ARCHIVO EXISTE
if [ ! -f "$archivo" ]; then
echo ""
echo "❌ El archivo '$archivo' no existe"
echo ""
echo "📋 ¿Buscabas alguno de estos?"
find . -name "*$(basename "$archivo")*" 2>/dev/null | head -5
exit 1
fi

# 3. MOSTRAR ESTADÍSTICAS DEL ARCHIVO
echo ""
echo "📋 ARCHIVO: $archivo"
echo "----------------------------------------"

# Tamaño
tamano=$(wc -l < "$archivo")
echo "📏 Líneas totales: $tamano"

# Última modificación
ultimo_commit=$(git log -1 --oneline -- "$archivo" | head -1)
echo "📝 Último cambio: $ultimo_commit"

# Cantidad de autores diferentes
autores=$(git log --format='%an' -- "$archivo" | sort -u | wc -l)
echo "👥 Autores diferentes: $autores"

# 4. MENÚ DE OPCIONES
echo ""
echo "¿Qué quieres ver?"
echo "1) Blame completo (quién escribió cada línea)"
echo "2) Blame resumido (solo líneas modificadas recientemente)"
echo "3) Estadísticas de contribución por autor"
echo "4) Buscar una línea o palabra específica"
read -p "Opción (1-4): " opcion

echo ""
echo "----------------------------------------"

case $opcion in
1)
# Blame completo
echo "📋 Blame de $archivo (primeras $lineas líneas):"
echo ""
git blame -L 1,"$lineas" "$archivo" 2>/dev/null

if [ "$tamano" -gt "$lineas" ]; then
echo ""
echo "⚠️  Mostrando primeras $lineas de $tamano líneas"
echo "   Para ver más: blame $archivo 100"
fi
;;

2)
# Blame de líneas recientes
echo "📋 Líneas modificadas en los últimos 30 días:"
echo ""
git blame --since="30 days ago" "$archivo" 2>/dev/null | head -"$lineas"

if [ -z "$(git blame --since="30 days ago" "$archivo" 2>/dev/null)" ]; then
echo "   No hay cambios recientes en este archivo"
fi
;;

3)
# Estadísticas por autor
echo "📊 CONTRIBUCIÓN POR AUTOR"
echo ""
echo "👥 Autores que modificaron '$archivo':"
echo "----------------------------------------"
git log --format='%an' -- "$archivo" | sort | uniq -c | sort -nr | while read count autor; do
echo "   $count commits - $autor"
done

echo ""
echo "📊 Porcentaje de líneas por autor:"
echo "----------------------------------------"
git blame --line-porcelain "$archivo" 2>/dev/null | \
grep "^author " | sort | uniq -c | sort -nr | \
while read count autor; do
nombre=$(echo "$autor" | sed 's/^author //')
porcentaje=$((count * 100 / tamano))
echo "   $porcentaje% ($count líneas) - $nombre"
done
;;

4)
# Buscar línea específica
read -p "Palabra o texto a buscar en el archivo: " texto
echo ""
echo "🔍 Buscando '$texto' en '$archivo'..."
echo "----------------------------------------"

# Buscar en el contenido actual
grep -n "$texto" "$archivo" | while read linea; do
num_linea=$(echo "$linea" | cut -d: -f1)
contenido=$(echo "$linea" | cut -d: -f2-)

# Encontrar quién modificó esa línea por última vez
autor_linea=$(git blame -L "$num_linea","$num_linea" "$archivo" 2>/dev/null | \
awk '{print $1" "$2" "$3}')

echo "   Línea $num_linea: $contenido"
echo "   👤 $autor_linea"
echo ""
done
;;

*)
echo "❌ Opción no válida"
exit 1
;;
esac

echo "=================================="
echo "✅ INVESTIGACIÓN COMPLETADA"
echo "=================================="
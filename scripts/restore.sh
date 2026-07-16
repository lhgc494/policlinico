#!/bin/bash
# =============================================
# NOMBRE:      restore
# DESCRIPCIÓN: Recupera un archivo borrado o vuelve a una versión anterior
# CUÁNDO USAR: Cuando borraste algo sin querer o necesitas volver atrás un archivo
# CATEGORÍA:   Emergencias
#
# EJEMPLOS DE USO:
#   restore archivo.txt
#   restore pacientes/models.py
# =============================================

echo "🔄 RECUPERANDO ARCHIVO"
echo "======================"

# 1. VALIDAR QUE HAY UN ARCHIVO
if [ -z "$1" ]; then
echo "❌ Debes indicar qué archivo quieres recuperar"
echo ""
echo "Uso: restore <nombre-archivo>"
echo ""
echo "Ejemplos:"
echo "  restore pacientes/models.py"
echo "  restore templates/base.html"
echo "  restore db.sqlite3"
exit 1
fi

archivo="$1"

# 2. VERIFICAR SI EL ARCHIVO EXISTE
if [ -f "$archivo" ]; then
echo ""
echo "⚠️  El archivo '$archivo' EXISTE actualmente"
echo "    ¿Qué quieres hacer?"
echo "    1) Ver historial de versiones del archivo"
echo "    2) Recuperar una versión anterior (sobrescribe la actual)"
echo "    3) Cancelar"
read -p "Opción (1-3): " opcion

case $opcion in
1)
echo ""
echo "📋 Historial de cambios de '$archivo':"
echo "----------------------------------------"
git log --oneline -- "$archivo"

echo ""
read -p "¿Quieres recuperar alguna versión? (s/n): " recuperar
if [ "$recuperar" != "s" ]; then
echo "⏭️  Cancelado"
exit 0
fi
read -p "Hash del commit a recuperar: " hash

echo ""
echo "📥 Recuperando '$archivo' del commit $hash..."
git checkout "$hash" -- "$archivo"
echo "✅ Archivo recuperado a la versión del commit $hash"
;;
2)
echo ""
echo "📋 Últimas versiones de '$archivo':"
echo "----------------------------------------"
git log --oneline -5 -- "$archivo"

echo ""
read -p "Hash del commit a recuperar: " hash

echo ""
echo "📥 Recuperando '$archivo' del commit $hash..."
git checkout "$hash" -- "$archivo"
echo "✅ Archivo recuperado a la versión del commit $hash"
;;
3)
echo "⏭️  Cancelado"
exit 0
;;
*)
echo "❌ Opción no válida"
exit 1
;;
esac
else
# 3. EL ARCHIVO NO EXISTE - FUE BORRADO
echo ""
echo "🔍 '$archivo' NO existe. Fue borrado."
echo ""

# Buscar en el historial
echo "📋 Buscando últimas versiones en el historial..."
echo "----------------------------------------"
git log --oneline -- "$archivo"

if [ $? -ne 0 ] || [ -z "$(git log --oneline -- "$archivo" 2>/dev/null)" ]; then
echo ""
echo "❌ No se encontró '$archivo' en el historial"
echo "   Posiblemente nunca fue commiteado"
echo ""
echo "💡 ¿Quizás está en otro lado?"
echo "   Busca con: find . -name \"$(basename "$archivo")\""
exit 1
fi

echo ""
read -p "¿Recuperar la última versión? (s/n): " recuperar_ultima

if [ "$recuperar_ultima" = "s" ]; then
echo ""
echo "📥 Recuperando última versión de '$archivo'..."
git checkout HEAD -- "$archivo" 2>/dev/null

if [ $? -eq 0 ]; then
echo "✅ Archivo recuperado: $archivo"
else
# Intentar con el último commit que lo tenía
ultimo_commit=$(git log --oneline -1 -- "$archivo" | cut -d' ' -f1)
git checkout "$ultimo_commit" -- "$archivo"
echo "✅ Archivo recuperado de commit $ultimo_commit"
fi
else
read -p "Hash del commit del cual recuperar: " hash
git checkout "$hash" -- "$archivo"
echo "✅ Archivo recuperado de commit $hash"
fi
fi

# 4. MOSTRAR ESTADO
echo ""
echo "📋 Estado del archivo recuperado:"
echo "----------------------------------------"
ls -lh "$archivo" 2>/dev/null
echo ""
echo "⚠️  Recuerda: el archivo está recuperado pero no commiteado"
echo "   Para guardarlo: save \"restore: recuperar $archivo\""
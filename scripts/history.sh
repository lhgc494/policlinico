#!/bin/bash
# =============================================
# NOMBRE:      history
# DESCRIPCIÓN: Muestra el historial de commits de forma visual y con opciones de filtro
# CUÁNDO USAR: Cuando necesitas entender qué pasó, revisar el trabajo del equipo o buscar un cambio
# CATEGORÍA:   Investigar
#
# EJEMPLOS DE USO:
#   history
#   history 10
#   history --autor Luis
# =============================================

echo "📋 HISTORIAL DEL PROYECTO"
echo "========================="

# 1. SI HAY ARGUMENTO NUMÉRICO, LIMITAR CANTIDAD
limite=""
if [ -n "$1" ] && [[ "$1" =~ ^[0-9]+$ ]]; then
limite="-$1"
echo "📋 Mostrando últimos $1 commits"
else
echo "📋 Mostrando todos los commits (puedes limitar: history 10)"
fi

echo ""

# 2. MENÚ DE OPCIONES
echo "¿Qué quieres ver?"
echo "1) Historial resumido (una línea por commit)"
echo "2) Historial con gráfico de ramas"
echo "3) Historial detallado (archivos modificados)"
echo "4) Commits de una persona específica"
echo "5) Commits que contengan una palabra"
echo "6) Commits de hoy"
read -p "Opción (1-6): " opcion

echo ""
echo "----------------------------------------"

case $opcion in
1)
# Historial simple
git log --oneline $limite
;;
2)
# Historial con gráfico
git log --oneline --graph --all --decorate $limite
;;
3)
# Historial detallado con archivos
git log --stat $limite
;;
4)
# Commits por autor
read -p "Nombre del autor: " autor
echo ""
echo "📋 Commits de '$autor':"
echo "----------------------------------------"
git log --oneline --author="$autor" $limite

echo ""
echo "📊 Estadísticas de '$autor':"
echo "----------------------------------------"
total=$(git log --oneline --author="$autor" | wc -l)
echo "   Total commits: $total"
;;
5)
# Buscar en mensajes
read -p "Palabra a buscar: " palabra
echo ""
echo "📋 Commits que contienen '$palabra':"
echo "----------------------------------------"
git log --oneline --grep="$palabra" $limite
;;
6)
# Commits de hoy
echo "📋 Commits de hoy ($(date '+%Y-%m-%d')):"
echo "----------------------------------------"
git log --oneline --since="midnight" $limite

total_hoy=$(git log --oneline --since="midnight" | wc -l)
echo ""
echo "📊 Total commits hoy: $total_hoy"
;;
*)
echo "❌ Opción no válida. Mostrando historial resumido por defecto..."
git log --oneline $limite
;;
esac

# 3. RESUMEN ADICIONAL
echo ""
echo "=================================="
echo "✅ Historial mostrado"
echo "=================================="
echo ""
echo "💡 Otros comandos útiles:"
echo "   history 20        ← Últimos 20 commits"
echo "   search            ← Buscar en commits"
echo "   blame archivo.py  ← Ver quién cambió cada línea"
#!/bin/bash
# =============================================
# NOMBRE:      dev.sh
# DESCRIPCIÓN: Menú maestro para gestionar todo el proyecto con Git
# CUÁNDO USAR: A diario, para cualquier operación del proyecto
# CATEGORÍA:   Menú Principal
#
# EJEMPLOS DE USO:
#   ./dev.sh
#   ./dev.sh save "feat: nuevo cambio"
#   ./dev.sh feature historia-clinica
# =============================================

# COLORES (para hacerlo más bonito)
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
AZUL='\033[0;34m'
CIAN='\033[0;36m'
SIN_COLOR='\033[0m'
NEGRITA='\033[1m'

# FUNCIONES AUXILIARES
mostrar_titulo() {
clear
echo -e "${AZUL}====================================${SIN_COLOR}"
echo -e "${NEGRITA}   🏥 POLICLÍNICO - MENÚ PRINCIPAL${SIN_COLOR}"
echo -e "${AZUL}====================================${SIN_COLOR}"
echo ""
}

mostrar_menu() {
echo -e "${AMARILLO}📋 DIARIO:${SIN_COLOR}"
echo "   1) save       - Guardar cambios y subir a GitHub"
echo "   2) status     - Ver estado del proyecto"
echo "   3) update     - Actualizar desde GitHub"
echo ""
echo -e "${AMARILLO}🌿 RAMAS:${SIN_COLOR}"
echo "   4) feature    - Crear nueva funcionalidad"
echo "   5) switch     - Cambiar de rama"
echo "   6) cleanup    - Limpiar ramas viejas"
echo ""
echo -e "${AMARILLO}🔄 FUSIONAR:${SIN_COLOR}"
echo "   7) merge      - Fusionar rama a main"
echo "   8) finish     - Finalizar funcionalidad actual"
echo ""
echo -e "${AMARILLO}🗄️ ALMACENAR:${SIN_COLOR}"
echo "   9) stash      - Guardar cambios temporalmente"
echo "   10) unstash   - Recuperar cambios guardados"
echo ""
echo -e "${AMARILLO}🆘 EMERGENCIAS:${SIN_COLOR}"
echo "   11) undo      - Deshacer último commit"
echo "   12) restore   - Recuperar archivo borrado"
echo "   13) abort     - Cancelar merge/rebase"
echo ""
echo -e "${AMARILLO}🔍 INVESTIGAR:${SIN_COLOR}"
echo "   14) history   - Ver historial de commits"
echo "   15) search    - Buscar en el historial"
echo "   16) blame     - Ver quién modificó cada línea"
echo ""
echo -e "${AMARILLO}🏷️ VERSIONADO:${SIN_COLOR}"
echo "   17) release   - Crear nueva versión"
echo "   18) hotfix    - Arreglo de emergencia"
echo ""
echo -e "${AMARILLO}🚀 DESPLIEGUE:${SIN_COLOR}"
echo "   19) deploy    - Desplegar a producción"
echo "   20) setup     - Configurar proyecto recién clonado"
echo ""
echo -e "${ROJO}0) Salir${SIN_COLOR}"
echo ""
}

ejecutar_opcion() {
case $1 in
1) save "$2" ;;
2) status ;;
3) update ;;
4) feature "$2" ;;
5)
if [ -z "$2" ]; then
echo -e "${CIAN}📋 Ramas disponibles:${SIN_COLOR}"
git branch -a
echo ""
read -p "¿A qué rama quieres cambiar? " rama
switch "$rama"
else
switch "$2"
fi
;;
6) cleanup ;;
7)
if [ -z "$2" ]; then
echo -e "${CIAN}📋 Ramas disponibles:${SIN_COLOR}"
git branch
echo ""
read -p "¿Qué rama quieres fusionar a main? " rama
merge "$rama"
else
merge "$2"
fi
;;
8) finish ;;
9)
if [ -z "$2" ]; then
stash
else
stash "$2"
fi
;;
10) unstash ;;
11) undo ;;
12)
if [ -z "$2" ]; then
read -p "¿Qué archivo quieres recuperar? " archivo
restore "$archivo"
else
restore "$2"
fi
;;
13) abort ;;
14) history ;;
15) search ;;
16)
if [ -z "$2" ]; then
read -p "¿Qué archivo quieres investigar? " archivo
blame "$archivo"
else
blame "$2"
fi
;;
17)
if [ -z "$2" ]; then
release
else
release "$2" "$3"
fi
;;
18)
if [ -z "$2" ]; then
hotfix
else
hotfix "$2"
fi
;;
19) deploy ;;
20) setup ;;
0)
echo -e "${VERDE}👋 ¡Hasta luego!${SIN_COLOR}"
exit 0
;;
*) echo -e "${ROJO}❌ Opción no válida${SIN_COLOR}" ;;
esac
}

# === MODO INTERACTIVO (sin argumentos) ===
if [ $# -eq 0 ]; then
while true; do
mostrar_titulo
mostrar_menu
read -p "Elige una opción: " opcion
ejecutar_opcion "$opcion"
echo ""
read -p "Presiona Enter para continuar..."
done
fi

# === MODO DIRECTO (con argumentos) ===
case $1 in
save|status|update|cleanup|finish|undo|abort|history|search|deploy|setup)
ejecutar_opcion $(echo "1:save 2:status 3:update 4:feature 5:switch 6:cleanup 7:merge 8:finish 9:stash 10:unstash 11:undo 12:restore 13:abort 14:history 15:search 16:blame 17:release 18:hotfix 19:deploy 20:setup" | grep -oP "\d+(?=:$1)" | head -1) "$2" "$3"
;;
feature|switch|merge|restore|blame|hotfix)
if [ -z "$2" ]; then
echo -e "${ROJO}❌ Esta opción necesita un argumento adicional${SIN_COLOR}"
echo "Ejemplo: ./dev.sh $1 <nombre>"
else
ejecutar_opcion $(echo "1:save 2:status 3:update 4:feature 5:switch 6:cleanup 7:merge 8:finish 9:stash 10:unstash 11:undo 12:restore 13:abort 14:history 15:search 16:blame 17:release 18:hotfix 19:deploy 20:setup" | grep -oP "\d+(?=:$1)" | head -1) "$2" "$3"
fi
;;
*)
echo -e "${AMARILLO}🏥 POLICLÍNICO - Menú Principal${SIN_COLOR}"
echo ""
echo "Uso:"
echo "  ./dev.sh                  ← Modo menú interactivo"
echo "  ./dev.sh <comando>        ← Modo directo"
echo ""
echo "Comandos disponibles:"
echo "  save \"mensaje\"            ← Guardar cambios"
echo "  status                    ← Ver estado"
echo "  update                    ← Actualizar proyecto"
echo "  feature <nombre>          ← Nueva funcionalidad"
echo "  switch <rama>             ← Cambiar rama"
echo "  cleanup                   ← Limpiar ramas"
echo "  merge <rama>              ← Fusionar rama"
echo "  finish                    ← Finalizar feature"
echo "  stash \"mensaje\"           ← Guardar temporal"
echo "  unstash                   ← Recuperar temporal"
echo "  undo                      ← Deshacer commit"
echo "  restore <archivo>         ← Recuperar archivo"
echo "  abort                     ← Cancelar operación"
echo "  history                   ← Ver historial"
echo "  search                    ← Buscar cambios"
echo "  blame <archivo>           ← Ver responsable"
echo "  release <version> \"desc\"  ← Crear versión"
echo "  hotfix <nombre>           ← Arreglo urgente"
echo "  deploy                    ← Desplegar"
echo "  setup                     ← Configurar proyecto"
;;
esac
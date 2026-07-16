#!/bin/bash
# =============================================
# NOMBRE:      git-global
# DESCRIPCIÓN: Configura Git por primera vez en una computadora nueva
# CUÁNDO USAR: Una sola vez al estrenar PC o después de formatear
# CATEGORÍA:   Setup Global
# =============================================

echo "🌍 Configurando Git globalmente..."
echo "=================================="

# 1. IDENTIDAD
# Obligatorio. Firma tus commits con tu nombre y email
echo ""
echo "📛 Configurando identidad..."
read -p "Tu nombre completo: " nombre
read -p "Tu email de GitHub: " email
git config --global user.name "$nombre"
git config --global user.email "$email"
echo "✅ Identidad: $nombre <$email>"

# 2. EDITOR
# El programa que se abre al escribir mensajes de commit largos
echo ""
echo "📝 Elige tu editor de código:"
echo "1) Sublime Text"
echo "2) VS Code"
echo "3) Nano (terminal)"
echo "4) Vim (terminal)"
read -p "Opción (1-4): " editor

case $editor in
1) git config --global core.editor "subl -w"
echo "✅ Editor: Sublime Text" ;;
2) git config --global core.editor "code --wait"
echo "✅ Editor: VS Code" ;;
3) git config --global core.editor "nano"
echo "✅ Editor: Nano" ;;
4) git config --global core.editor "vim"
echo "✅ Editor: Vim" ;;
*) echo "❌ Opción no válida, usando Nano por defecto"
git config --global core.editor "nano" ;;
esac

# 3. RAMA PRINCIPAL
# Define que la rama principal se llame "main"
git config --global init.defaultBranch main
echo "✅ Rama por defecto: main"

# 4. ALIAS
# Atajos para comandos largos
echo ""
echo "⚡ Configurando alias (atajos)..."

git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.last "log -1 HEAD"
git config --global alias.st "status -s"
git config --global alias.br "branch"
git config --global alias.co "checkout"
git config --global alias.ci "commit"
git config --global alias.unstage "reset HEAD --"
git config --global alias.visual "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --all"

echo "✅ Alias configurados: lg, undo, last, st, br, co, ci, unstage, visual"

# 5. COLORES
# Mejora la legibilidad en la terminal
git config --global color.ui auto
git config --global color.branch auto
git config --global color.diff auto
git config --global color.status auto
echo "✅ Colores activados"

# 6. PULL CON REBASE
# Evita commits de merge innecesarios al hacer pull
git config --global pull.rebase true
echo "✅ Pull con rebase activado"

# 7. PUSH POR DEFECTO
git config --global push.default simple
echo "✅ Push simple por defecto"

echo ""
echo "=================================="
echo "🌍 CONFIGURACIÓN GLOBAL COMPLETADA"
echo "=================================="
echo ""
echo "📋 Resumen de tu configuración:"
echo ""
git config --global --list



#!/bin/bash
# =============================================
# NOMBRE:      git-connect
# DESCRIPCIÓN: Conecta un proyecto local con un repositorio remoto en GitHub
# CUÁNDO USAR: Una vez por proyecto, al iniciarlo o al clonarlo manualmente
# CATEGORÍA:   Setup Global
# =============================================

echo "🔗 Conectando proyecto con GitHub..."
echo "=================================="

# 1. VERIFICAR QUE ES UN REPOSITORIO GIT
# Comprueba que existe la carpeta .git
if [ ! -d ".git" ]; then
echo "❌ No es un repositorio Git. Ejecuta primero: git init"
exit 1
fi
echo "✅ Repositorio Git detectado"

# 2. VERIFICAR SI YA TIENE REMOTO
# Si ya está conectado, avisa y pregunta si quiere cambiar
if git remote -v | grep -q "origin"; then
echo ""
echo "⚠️  Ya existe una conexión remota:"
git remote -v
echo ""
read -p "¿Quieres cambiar la URL? (s/n): " cambiar
if [ "$cambiar" = "s" ]; then
git remote remove origin
echo "🗑️  Conexión anterior eliminada"
else
echo "✅ Manteniendo conexión actual. Saliendo..."
exit 0
fi
fi

# 3. PEDIR DATOS
# Solicita usuario y nombre del repositorio
echo ""
read -p "Tu usuario de GitHub: " usuario
read -p "Nombre del repositorio: " repo

# 4. CONSTRUIR URL
# Soporta HTTPS (recomendado) y SSH
echo ""
echo "Tipo de conexión:"
echo "1) HTTPS (recomendado - usa contraseña o token)"
echo "2) SSH (usa clave SSH)"
read -p "Opción (1-2): " tipo

case $tipo in
1) url="https://github.com/$usuario/$repo.git"
echo "✅ Usando HTTPS" ;;
2) url="git@github.com:$usuario/$repo.git"
echo "✅ Usando SSH" ;;
*) echo "❌ Opción no válida. Usando HTTPS por defecto"
url="https://github.com/$usuario/$repo.git" ;;
esac

# 5. AÑADIR REMOTO
git remote add origin "$url"
echo "🔗 Remoto 'origin' añadido: $url"

# 6. PRIMER PUSH
# Sube la rama principal a GitHub
echo ""
echo "📤 Subiendo código a GitHub..."
echo ""

# Detectar rama actual
rama=$(git branch --show-current)

# Si no hay commits, crear el primero
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
echo "⚠️  No hay commits aún."
read -p "¿Quieres crear un primer commit? (s/n): " crear
if [ "$crear" = "s" ]; then
git add .
git commit -m "chore: primer commit"
echo "✅ Primer commit creado"
fi
fi

# Push
git push -u origin "$rama"
echo ""
echo "=================================="
echo "🔗 PROYECTO CONECTADO A GITHUB"
echo "=================================="
echo ""
echo "📋 Datos de conexión:"
echo "   Remoto:  origin"
echo "   URL:     $url"
echo "   Rama:    $rama"
echo ""
echo "🌐 Repositorio en: https://github.com/$usuario/$repo"
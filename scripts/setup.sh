#!/bin/bash
# =============================================
# NOMBRE:      setup
# DESCRIPCIÓN: Configura el proyecto recién clonado: dependencias, entorno, base de datos
# CUÁNDO USAR: Al clonar el proyecto por primera vez en una computadora
# CATEGORÍA:   Despliegue
#
# EJEMPLOS DE USO:
#   setup
#   (Se ejecuta una sola vez después de git clone)
# =============================================

echo "🔧 CONFIGURANDO PROYECTO"
echo "========================"

# 1. VERIFICAR QUE ES UN PROYECTO VÁLIDO
if [ ! -d ".git" ]; then
echo "❌ No es un repositorio Git"
echo "   Clona primero: git clone <url>"
exit 1
fi
echo "✅ Repositorio Git detectado"

# 2. DETECTAR TIPO DE PROYECTO
echo ""
echo "🔍 Detectando tipo de proyecto..."
echo "----------------------------------------"

es_python=false
es_node=false
es_django=false

if [ -f "requirements.txt" ]; then
es_python=true
echo "🐍 Proyecto Python detectado"
fi

if [ -f "manage.py" ]; then
es_django=true
echo "🎯 Proyecto Django detectado"
fi

if [ -f "package.json" ]; then
es_node=true
echo "📦 Proyecto Node.js detectado"
fi

# 3. ENTORNO VIRTUAL (PYTHON)
if $es_python; then
echo ""
echo "🐍 Configurando entorno Python..."
echo "----------------------------------------"

# Crear entorno virtual
if [ ! -d "venv" ]; then
echo "📦 Creando entorno virtual..."
python3 -m venv venv
echo "✅ Entorno virtual creado"
else
echo "✅ Entorno virtual ya existe"
fi

# Activar
source venv/bin/activate
echo "✅ Entorno virtual activado"

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias..."
pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "✅ Dependencias instaladas"
fi

# 4. DEPENDENCIAS NODE
if $es_node; then
echo ""
echo "📦 Configurando Node.js..."
echo "----------------------------------------"

if [ ! -d "node_modules" ]; then
echo "📥 Instalando dependencias Node..."
npm install
echo "✅ Dependencias Node instaladas"
else
echo "✅ Dependencias Node ya existen"
fi
fi

# 5. VARIABLES DE ENTORNO
echo ""
echo "🔑 Configurando variables de entorno..."
echo "----------------------------------------"

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
cp .env.example .env
echo "✅ Archivo .env creado desde .env.example"
echo "⚠️  RECUERDA editar .env con tus valores reales"
echo "   Editor: nano .env"
elif [ -f ".env" ]; then
echo "✅ Archivo .env ya existe"
else
echo "⚠️  No se encontró .env.example ni .env"
echo "   Crea uno manualmente si es necesario"
fi

# 6. BASE DE DATOS (DJANGO)
if $es_django; then
echo ""
echo "🗄️  Configurando base de datos..."
echo "----------------------------------------"

echo "📋 Aplicando migraciones..."
python manage.py migrate
echo "✅ Migraciones aplicadas"

# Preguntar por superusuario
echo ""
read -p "¿Crear superusuario de Django? (s/n): " crear_super
if [ "$crear_super" = "s" ]; then
python manage.py createsuperuser
fi

# Cargar datos iniciales (fixtures)
if [ -d "fixtures" ] && [ "$(ls -A fixtures 2>/dev/null)" ]; then
echo ""
read -p "¿Cargar datos iniciales (fixtures)? (s/n): " cargar
if [ "$cargar" = "s" ]; then
echo "📥 Cargando datos iniciales..."
for fixture in fixtures/*.json; do
python manage.py loaddata "$fixture"
echo "   ✅ $(basename "$fixture")"
done
echo "✅ Datos iniciales cargados"
fi
fi
fi

# 7. SCRIPTS DEL PROYECTO
echo ""
echo "📜 Configurando scripts..."
echo "----------------------------------------"

if [ -d "scripts" ]; then
chmod +x scripts/*.sh 2>/dev/null
echo "✅ Permisos de ejecución aplicados a scripts/"
fi

# 8. CONFIGURACIÓN DE GIT LOCAL
echo ""
echo "🔧 Configurando Git local..."
echo "----------------------------------------"

# Verificar remote
if git remote -v | grep -q "origin"; then
echo "✅ Conectado a GitHub:"
git remote -v | head -1
else
echo "⚠️  No hay remoto configurado"
read -p "¿Configurar GitHub ahora? (s/n): " config_remote
if [ "$config_remote" = "s" ]; then
read -p "URL del repositorio: " url
git remote add origin "$url"
echo "✅ Remoto configurado"
fi
fi

# 9. VERIFICAR ESTRUCTURA
echo ""
echo "📂 Estructura del proyecto:"
echo "----------------------------------------"
ls -la --color=auto

# 10. RESUMEN FINAL
echo ""
echo "=================================="
echo "✅ PROYECTO CONFIGURADO"
echo "=================================="
echo ""
echo "📋 Próximos pasos:"
echo "   1. Editar .env:          nano .env"
echo "   2. Iniciar servidor:     python manage.py runserver"
echo "   3. Ver estado:           status"
echo "   4. Empezar a trabajar:   feature <nombre>"
echo ""
echo "💡 Scripts disponibles:"
echo "   Diario:     save, status, update"
echo "   Ramas:      feature, switch, cleanup"
echo "   Fusionar:   merge, finish"
echo "   Emergencias: undo, restore, abort"
echo "   Versionado: release, hotfix"
echo "   Despliegue: deploy"
echo ""
echo "🎉 ¡Listo para trabajar!"
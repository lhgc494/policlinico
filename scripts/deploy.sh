#!/bin/bash
# =============================================
# NOMBRE:      deploy
# DESCRIPCIÓN: Despliega el proyecto en el servidor de producción
# CUÁNDO USAR: Después de crear una release o cuando hay cambios listos para producción
# CATEGORÍA:   Despliegue
#
# EJEMPLOS DE USO:
#   deploy
#   deploy produccion
# =============================================

echo "🚀 DESPLEGANDO A PRODUCCIÓN"
echo "============================"

# 1. VERIFICAR QUE ESTAMOS EN MAIN
rama=$(git branch --show-current)
if [ "$rama" != "main" ]; then
echo "⚠️  No estás en main (estás en '$rama')"
echo "    Solo se despliega desde main"
echo ""
read -p "¿Cambiar a main? (s/n): " cambiar
if [ "$cambiar" = "s" ]; then
git checkout main
echo "✅ Cambiado a main"
else
echo "❌ Deploy cancelado"
exit 1
fi
fi

# 2. VERIFICAR CAMBIOS PENDIENTES
if ! git diff --quiet || ! git diff --cached --quiet; then
echo ""
echo "⚠️  Tienes cambios sin guardar"
read -p "¿Guardarlos antes de desplegar? (s/n): " guardar
if [ "$guardar" = "s" ]; then
read -p "Mensaje del commit: " mensaje
git add .
git commit -m "$mensaje"
echo "✅ Cambios guardados"
else
echo "⚠️  Continuando sin guardar (solo se desplegará lo commiteado)"
fi
fi

# 3. ACTUALIZAR MAIN
echo ""
echo "⬇️  Actualizando main desde GitHub..."
git pull origin main
echo "✅ Main actualizado"

# 4. MOSTRAR QUÉ SE VA A DESPLEGAR
echo ""
echo "📋 Cambios a desplegar:"
echo "----------------------------------------"

# Buscar último tag
ultimo_tag=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -n "$ultimo_tag" ]; then
echo "   Desde $ultimo_tag hasta ahora:"
git log --oneline "$ultimo_tag"..HEAD
total=$(git log --oneline "$ultimo_tag"..HEAD | wc -l)
else
echo "   (No hay tags anteriores)"
git log --oneline -10
total=$(git log --oneline -10 | wc -l)
fi

echo ""
echo "📊 Commits a desplegar: $total"

# 5. CONFIRMAR
echo ""
echo "⚠️  ATENCIÓN: Esto afectará el servidor de producción"
echo "   Asegúrate de que:"
echo "   ✅ Los tests pasaron"
echo "   ✅ Probaste en entorno de desarrollo"
echo "   ✅ Tienes backup reciente"
echo ""
read -p "¿Confirmar despliegue? (ESCRIBE 'desplegar' para confirmar): " confirmar

if [ "$confirmar" != "desplegar" ]; then
echo "⏭️  Deploy cancelado"
exit 0
fi

# 6. SUBIR CAMBIOS A GITHUB
echo ""
echo "📤 Subiendo cambios a GitHub..."
git push origin main
echo "✅ Cambios en GitHub"

# 7. CONECTAR AL SERVIDOR
echo ""
echo "🖥️  Conectando al servidor..."

# Verificar si hay configuración de servidor
if [ -z "$PRODUCTION_HOST" ]; then
echo ""
echo "⚠️  No se detectó variable PRODUCTION_HOST"
echo "    Configúrala con: export PRODUCTION_HOST='usuario@servidor.com'"
echo ""
read -p "Dirección del servidor (usuario@ip): " servidor
else
servidor="$PRODUCTION_HOST"
echo "📍 Servidor: $servidor"
fi

# 8. EJECUTAR DEPLOY EN SERVIDOR
echo ""
echo "🚀 Ejecutando despliegue en $servidor..."
echo "----------------------------------------"

ssh "$servidor" << 'ENDSSH'
echo "📥 Entrando al servidor..."

# Ir al directorio del proyecto
cd /opt/policlinico || cd ~/policlinico || {
echo "❌ No se encontró el directorio del proyecto"
exit 1
}

echo "📍 Directorio: $(pwd)"

# Actualizar código
echo "📥 Descargando cambios..."
git pull origin main

# Activar entorno virtual (Python)
if [ -f "venv/bin/activate" ]; then
source venv/bin/activate
echo "✅ Entorno virtual activado"
fi

# Instalar dependencias
if [ -f "requirements.txt" ]; then
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt --quiet
echo "✅ Dependencias instaladas"
fi

# Migraciones
if [ -f "manage.py" ]; then
echo "🗄️  Aplicando migraciones..."
python manage.py migrate --noinput
echo "✅ Migraciones aplicadas"

# Archivos estáticos
echo "📂 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput 2>/dev/null
echo "✅ Estáticos recopilados"
fi

# Reiniciar servicio
echo "🔄 Reiniciando servicio..."
sudo systemctl restart policlinico 2>/dev/null || \
sudo systemctl restart nginx 2>/dev/null || \
echo "⚠️  No se pudo reiniciar el servicio automáticamente"

echo "✅ Servidor actualizado"
ENDSSH

# 9. RESULTADO
if [ $? -eq 0 ]; then
echo ""
echo "=================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "=================================="
echo ""
echo "📍 Servidor: $servidor"
echo "📊 Commits desplegados: $total"
echo "🕐 Hora: $(date '+%Y-%m-%d %H:%M')"
echo ""
echo "💡 Verificar:"
echo "   - Entra a la web y prueba funcionalidades"
echo "   - Revisa logs: ssh $servidor 'tail -f /var/log/policlinico.log'"
else
echo ""
echo "❌ Error en el despliegue"
echo "   Revisa la conexión y los logs del servidor"
fi
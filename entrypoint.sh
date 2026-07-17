#!/bin/bash
echo "🔄 Iniciando configuración del policlínico..."

echo "📦 PASO 1: Aplicando migraciones..."
python manage.py migrate --noinput

# Verificar si la base de datos ya tiene datos (usando usuarios como referencia)
echo "🔍 Verificando si la base de datos ya contiene datos..."
USER_COUNT=$(python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())" 2>/dev/null | tail -1)

if [ "$USER_COUNT" -eq "0" ]; then
    echo "📥 Base de datos vacía. Cargando fixtures..."
    FIXTURES_DIR="/app/fixtures"
    
    # Verificar que el directorio existe
    if [ -d "$FIXTURES_DIR" ]; then
        # Cargar en orden numérico
        for fixture in $(ls -1 $FIXTURES_DIR/*.json 2>/dev/null | sort); do
            if [ -f "$fixture" ]; then
                echo "  📌 Cargando $(basename $fixture)..."
                if python manage.py loaddata "$fixture"; then
                    echo "  ✅ $(basename $fixture) cargado correctamente"
                else
                    echo "  ⚠️  Error en $fixture (continuando...)"
                fi
            fi
        done
    else
        echo "⚠️  Directorio de fixtures no encontrado: $FIXTURES_DIR"
    fi
else
    echo "✅ Base de datos ya contiene $USER_COUNT usuarios. Omitiendo carga de fixtures."
fi

echo "🎉 Configuración completada exitosamente"
exec "$@"
# Usar imagen oficial de Python
FROM python:3.10-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings_production

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (versión corregida para weasyprint)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt /app/

# Instalar dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Verificar que Django se instaló correctamente
RUN python -c "import django; print(f'✅ Django {django.get_version()} instalado correctamente')"

# Copiar el resto del proyecto
COPY . /app/

# Verificar que manage.py existe
RUN test -f manage.py && echo "✅ manage.py encontrado" || echo "❌ manage.py NO encontrado"

# Dar permisos de ejecución
RUN chmod +x manage.py

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]

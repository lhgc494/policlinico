#!/bin/bash
cd ~/policlinico

echo "=== CORRECCIÓN COMPLETA DE finalizar_pago ==="

# 1. Hacer backup
cp farmacia/views.py farmacia/views.py.backup_finalizar_pago

# 2. Corregir Exception
sed -i 's/except Exceptn as e:/except Exception as e:/g' farmacia/views.py

# 3. Buscar y corregir TODAS las URLs sin namespace en esta función
echo "Buscando URLs en finalizar_pago..."
START=$(grep -n "def finalizar_pago" farmacia/views.py | cut -d: -f1)
if [ ! -z "$START" ]; then
    END=$((START + 200))
    
    # Extraer la función
    sed -n "${START},${END}p" farmacia/views.py > /tmp/funcion.txt
    
    # Buscar URLs problemáticas
    echo "URLs encontradas en la función:"
    grep -o "redirect('[^']*'" /tmp/funcion.txt | sed "s/redirect('//g" | sed "s/'//g"
    
    # Corregir cada una
    for url in $(grep -o "redirect('[^']*'" /tmp/funcion.txt | sed "s/redirect('//g" | sed "s/'//g"); do
        echo "Corrigiendo: $url → farmacia:$url"
        sed -i "${START},${END}s/redirect('${url}'/redirect('farmacia:${url}'/g" farmacia/views.py
    done
fi

echo ""
echo "=== VERIFICACIÓN ==="
echo "Buscando 'Exceptn':"
grep -n "Exceptn" farmacia/views.py || echo "✅ Corregido"

echo ""
echo "Buscando redirect sin namespace en finalizar_pago:"
if [ ! -z "$START" ]; then
    END=$((START + 200))
    sed -n "${START},${END}p" farmacia/views.py | grep -n "redirect" | grep -v "farmacia:" || echo "✅ Todos corregidos"
fi

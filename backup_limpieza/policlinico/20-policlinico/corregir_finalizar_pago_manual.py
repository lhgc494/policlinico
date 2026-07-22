#!/usr/bin/env python3
import re

with open('farmacia/views.py', 'r') as f:
    content = f.read()

# Encontrar la sección problemática
pattern = r"(if recetas_atendidas and 'venta' in recetas_atendidas\[0\]:\s*\n\s*return redirect\('farmacia:ticket_venta', id=recetas_atendidas\[0\]\['venta'\]\.id\))"

match = re.search(pattern, content)
if match:
    print("Encontrada la sección problemática")
    
    # Reemplazar con lógica mejorada
    replacement = """if recetas_atendidas:
                for item in recetas_atendidas:
                    if 'venta' in item:
                        return redirect('farmacia:ticket_venta', id=item['venta'].id)
                # Si no encontró venta, redirigir a recetas pendientes
                messages.success(request, '✅ Pago procesado exitosamente.')
                return redirect('farmacia:recetas_pendientes')"""
    
    new_content = content.replace(match.group(1), replacement)
    
    with open('farmacia/views.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Corregido manualmente")
else:
    print("⚠️ No se encontró el patrón. Buscando alternativa...")
    
    # Buscar por líneas cercanas
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'if recetas_atendidas' in line and 'venta' in line:
            print(f"Encontrado en línea {i+1}: {line.strip()}")
            # Mostrar contexto
            for j in range(max(0, i-2), min(len(lines), i+5)):
                print(f"{j+1}: {lines[j]}")
            break

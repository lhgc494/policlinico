import sys

with open('farmacia/views.py', 'r') as f:
    lines = f.readlines()

# Buscar la línea problemática
for i, line in enumerate(lines):
    if 'if recetas_atendidas and' in line and 'venta' in line:
        print(f"Encontrado en línea {i+1}")
        
        # Ver indentación actual
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        # Reemplazar las líneas
        lines[i] = indent_str + "if recetas_atendidas:\n"
        lines.insert(i+1, indent_str + "    for item in recetas_atendidas:\n")
        lines.insert(i+2, indent_str + "        if 'venta' in item:\n")
        lines.insert(i+3, indent_str + "            return redirect('farmacia:ticket_venta', id=item['venta'].id)\n")
        lines.insert(i+4, indent_str + "    # Si no encontró venta, redirigir a recetas pendientes\n")
        lines.insert(i+5, indent_str + "    messages.success(request, '✅ Pago procesado exitosamente.')\n")
        lines.insert(i+6, indent_str + "    return redirect('farmacia:recetas_pendientes')\n")
        
        # Eliminar la línea siguiente (el return original)
        if i+7 < len(lines) and 'return redirect' in lines[i+7]:
            lines[i+7] = ''
        
        break

# Guardar
with open('farmacia/views.py', 'w') as f:
    f.writelines(lines)

print("✅ Corregido")

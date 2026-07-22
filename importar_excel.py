# /home/luis/policlinico/importar_excel.py
import os
import django
import pandas as pd
from decimal import Decimal
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from farmacia.models import Medicamento, Categoria, Proveedor
from django.contrib.auth.models import User

def obtener_o_crear_categoria(nombre_grupo):
    """Obtiene o crea una categoría por nombre"""
    if not nombre_grupo or pd.isna(nombre_grupo):
        return None
    
    nombre = str(nombre_grupo).strip()
    if not nombre:
        return None
    
    categoria, created = Categoria.objects.get_or_create(
        nombre__iexact=nombre,
        defaults={'nombre': nombre, 'descripcion': f'Categoría {nombre}'}
    )
    if created:
        print(f"  🏷️  Categoría creada: {nombre}")
    return categoria

def calcular_precio_caja(row, precio_unitario, cantidad_por_caja):
    """Calcula precio por caja según la fórmula del Excel"""
    try:
        # Intentar obtener el precio por caja del Excel
        precio_caja_raw = row.get('Precio por caja')
        if pd.notna(precio_caja_raw) and str(precio_caja_raw) != '#DIV/0!':
            return Decimal(str(precio_caja_raw))
    except:
        pass
    
    # Si no hay, aplicar la lógica: =IF(cantidad>1,(cantidad*precio)*0.95,precio)
    if cantidad_por_caja and cantidad_por_caja > 1:
        return (cantidad_por_caja * precio_unitario) * Decimal('0.95')
    return precio_unitario

def importar_medicamentos(excel_path):
    """
    Importa medicamentos desde un archivo Excel
    """
    print("="*60)
    print(f"📂 IMPORTADOR DE INVENTARIO - FARMACIA")
    print("="*60)
    print(f"📂 Leyendo archivo: {excel_path}")

    # Verificar que el archivo existe
    if not os.path.exists(excel_path):
        print(f"❌ ERROR: El archivo no existe en la ruta especificada")
        return

    # Leer Excel
    try:
        df = pd.read_excel(excel_path, sheet_name='Hoja1')
        print(f"📊 Total de filas en Excel: {len(df)}")
        print(f"📋 Columnas encontradas: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return

    # Obtener usuario por defecto
    usuario, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'is_superuser': True, 
            'is_staff': True,
            'email': 'admin@localhost'
        }
    )
    print(f"👤 Usuario: {usuario.username}")

    # Contadores
    creados = 0
    actualizados = 0
    errores = 0
    categorias_creadas = 0
    sin_categoria = 0
    filas_procesadas = 0

    print("\n" + "="*60)
    print("📦 PROCESANDO MEDICAMENTOS...")
    print("="*60)

    # Recorrer cada fila del Excel
    for index, row in df.iterrows():
        filas_procesadas += 1
        
        try:
            # Saltar filas vacías (sin código)
            codigo_raw = row.get('Código')
            if pd.isna(codigo_raw):
                continue

            # Obtener o crear categoría
            grupo = row.get('Grupo de productos', '')
            categoria = obtener_o_crear_categoria(grupo)
            if categoria and not hasattr(categoria, '_created'):
                pass  # Ya existía
            elif categoria:
                categorias_creadas += 1

            # Procesar precios (manejar #DIV/0!)
            precio_raw = row.get('Precio')
            try:
                if pd.isna(precio_raw) or str(precio_raw) == '#DIV/0!':
                    precio_venta = Decimal('0')
                else:
                    precio_venta = Decimal(str(precio_raw))
            except:
                precio_venta = Decimal('0')

            # Procesar costo
            costo_raw = row.get('Costo')
            try:
                if pd.isna(costo_raw):
                    precio_compra = Decimal('0')
                else:
                    precio_compra = Decimal(str(costo_raw))
            except:
                precio_compra = Decimal('0')

            # Procesar cantidad
            cantidad_raw = row.get('Cant.')
            try:
                if pd.isna(cantidad_raw):
                    stock_actual = 0
                else:
                    stock_actual = int(float(cantidad_raw))
            except:
                stock_actual = 0

            # Procesar cantidad por caja
            cant_caja_raw = row.get('Cantidad por caja')
            try:
                if pd.isna(cant_caja_raw):
                    cantidad_por_caja = 1
                else:
                    cantidad_por_caja = int(float(cant_caja_raw))
            except:
                cantidad_por_caja = 1

            # Procesar fecha de vencimiento
            fecha_raw = row.get('Fecha de vencimieto')
            fecha_vencimiento = None
            if pd.notna(fecha_raw):
                try:
                    fecha_vencimiento = pd.to_datetime(fecha_raw).date()
                except:
                    print(f"  ⚠️ Fecha inválida para código {codigo_raw}: {fecha_raw}")

            # Procesar código de barras - CRÍTICO: debe ser NULL si está vacío
            codigo_barras_raw = row.get('Codigo de barra', '')
            codigo_barras = None
            if pd.notna(codigo_barras_raw) and str(codigo_barras_raw).strip():
                codigo_barras = str(codigo_barras_raw).strip()
            # Si está vacío, se queda como None (NULL en BD)

            # Mapear datos según el modelo
            datos = {
                'codigo': str(codigo_raw).strip(),
                'codigo_barras': codigo_barras,  # ✅ Ahora es None si está vacío
                'categoria': categoria,
                'nombre_comercial': str(row.get('Comercial', '')).strip()[:200] or f"Producto {codigo_raw}",
                'principio_activo': str(row.get('Compuesto', '')).strip()[:200] or None,
                'forma_farmaceutica': str(row.get('Presentacion', '')).strip()[:100] or None,
                'registro_sanitario': str(row.get('REGISTRO SANITARIO', '')).strip()[:50] or None,
                'cantidad_por_caja': cantidad_por_caja,
                'lote': str(row.get('Lote', '')).strip()[:50] or None,
                'fecha_vencimiento': fecha_vencimiento,
                'fabricante': None,  # No está en Excel
                'proveedor': None,    # No está en Excel
                'stock_actual': max(0, stock_actual),  # No negativo
                'stock_minimo': 10,   # Valor por defecto
                'precio_compra': precio_compra,
                'precio_venta': precio_venta,
                'precio_por_caja': calcular_precio_caja(row, precio_venta, cantidad_por_caja),
                'activo': True,
                'creado_por': usuario,
            }

            # Validar código
            if not datos['codigo']:
                print(f"  ⚠️ Fila {index + 2}: Sin código, se omite")
                continue

            # Buscar si ya existe
            medicamento, created = Medicamento.objects.update_or_create(
                codigo=datos['codigo'],
                defaults=datos
            )

            if created:
                creados += 1
                print(f"✅ [{creados}] CREADO: {medicamento.nombre_comercial} (Cód: {medicamento.codigo})")
            else:
                actualizados += 1
                print(f"🔄 [{actualizados}] ACTUALIZADO: {medicamento.nombre_comercial} (Cód: {medicamento.codigo})")

        except Exception as e:
            errores += 1
            print(f"❌ ERROR en fila {index + 2}: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("📊 RESUMEN FINAL DE IMPORTACIÓN")
    print("="*60)
    print(f"📦 Total filas procesadas: {filas_procesadas}")
    print(f"🏷️  Categorías creadas: {categorias_creadas}")
    print(f"🚫 Sin categoría: {sin_categoria}")
    print(f"✅ Medicamentos creados: {creados}")
    print(f"🔄 Medicamentos actualizados: {actualizados}")
    print(f"❌ Errores: {errores}")
    
    # Verificación final
    total_medicamentos = Medicamento.objects.count()
    print(f"\n📈 Total de medicamentos en BD después de importación: {total_medicamentos}")
    print("="*60)

if __name__ == "__main__":
    import sys
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "medicamentos_reales.xlsx"
    importar_medicamentos(excel_path)

# /home/luis/policlinico/importar_excel.py (versión mejorada)

import os
import django
import pandas as pd
from decimal import Decimal
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from farmacia.models import Medicamento, Categoria
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

def convertir_fecha(valor):
    """Convierte varios formatos de fecha a objeto date"""
    if pd.isna(valor):
        return None
    try:
        if isinstance(valor, datetime):
            return valor.date()
        return pd.to_datetime(valor).date()
    except:
        return None

def limpiar_valor_texto(valor):
    """Limpia valores de texto, retorna None si está vacío"""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto if texto else None

def importar_medicamentos(excel_path):
    print("="*60)
    print("📂 IMPORTADOR DE INVENTARIO - VERSIÓN MEJORADA")
    print("="*60)
    print(f"📂 Leyendo archivo: {excel_path}")

    if not os.path.exists(excel_path):
        print(f"❌ ERROR: El archivo no existe")
        return

    try:
        df = pd.read_excel(excel_path)
        print(f"📊 Total de filas en Excel: {len(df)}")
        print(f"📋 Columnas encontradas: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Error leyendo Excel: {e}")
        return

    usuario, _ = User.objects.get_or_create(
        username='admin',
        defaults={'is_superuser': True, 'is_staff': True}
    )

    stats = {
        'creados': 0, 'actualizados': 0, 'errores': 0,
        'categorias_creadas': 0, 'sin_categoria': 0,
        'con_registro': 0, 'sin_registro': 0,
        'sin_nombre': 0
    }

    print("\n📦 PROCESANDO MEDICAMENTOS...\n")

    for index, row in df.iterrows():
        try:
            codigo_raw = row.get('Código')
            if pd.isna(codigo_raw):
                continue

            # ============================================
            # 1. CATEGORÍA
            # ============================================
            grupo = row.get('Grupo de productos', '')
            categoria = obtener_o_crear_categoria(grupo)
            if categoria:
                stats['categorias_creadas'] += 1
            else:
                stats['sin_categoria'] += 1

            # ============================================
            # 2. NOMBRE COMERCIAL (¡MEJORADO!)
            # ============================================
            nombre_raw = row.get('comercial')
            if pd.isna(nombre_raw) or str(nombre_raw).strip() == '':
                nombre_comercial = f"Producto sin nombre - Código {codigo_raw}"
                stats['sin_nombre'] += 1
                print(f"  ⚠️ Fila {index+2}: Sin nombre comercial, se usará: {nombre_comercial}")
            else:
                nombre_comercial = str(nombre_raw).strip()

            # ============================================
            # 3. PRINCIPIO ACTIVO
            # ============================================
            principio_raw = row.get('compuesto')
            principio_activo = limpiar_valor_texto(principio_raw)

            # ============================================
            # 4. PRESENTACIÓN
            # ============================================
            presentacion_raw = row.get('presentacion')
            forma_farmaceutica = limpiar_valor_texto(presentacion_raw)

            # ============================================
            # 5. REGISTRO SANITARIO
            # ============================================
            registro_raw = row.get('REGISTRO SANITARIO')
            registro_sanitario = limpiar_valor_texto(registro_raw)
            if registro_sanitario:
                stats['con_registro'] += 1
            else:
                stats['sin_registro'] += 1

            # ============================================
            # 6. CANTIDAD POR CAJA
            # ============================================
            try:
                cant_caja_raw = row.get('Cantidad por caja')
                cantidad_por_caja = int(float(cant_caja_raw)) if pd.notna(cant_caja_raw) else 1
            except:
                cantidad_por_caja = 1

            # ============================================
            # 7. LOTE
            # ============================================
            lote_raw = row.get('Lote')
            lote = limpiar_valor_texto(lote_raw)

            # ============================================
            # 8. FECHA VENCIMIENTO
            # ============================================
            fecha_raw = row.get('Fecha de vencimieto ')
            fecha_vencimiento = convertir_fecha(fecha_raw)

            # ============================================
            # 9. STOCK ACTUAL
            # ============================================
            try:
                cantidad_raw = row.get('Cant.')
                stock_actual = int(float(cantidad_raw)) if pd.notna(cantidad_raw) else 0
            except:
                stock_actual = 0

            # ============================================
            # 10. PRECIO COMPRA
            # ============================================
            try:
                costo_raw = row.get('Costo')
                precio_compra = Decimal(str(costo_raw)) if pd.notna(costo_raw) else Decimal('0')
            except:
                precio_compra = Decimal('0')

            # ============================================
            # 11. PRECIO VENTA
            # ============================================
            try:
                precio_raw = row.get('precio')
                precio_venta = Decimal(str(precio_raw)) if pd.notna(precio_raw) else Decimal('0')
            except:
                precio_venta = Decimal('0')

            # ============================================
            # 12. PRECIO POR CAJA
            # ============================================
            try:
                precio_caja_raw = row.get('Precio por caja')
                if pd.notna(precio_caja_raw) and str(precio_caja_raw) not in ['#DIV/0!', '']:
                    precio_por_caja = Decimal(str(precio_caja_raw))
                else:
                    # Calcular según lógica de negocio
                    if cantidad_por_caja >= 3:
                        precio_por_caja = (cantidad_por_caja * precio_venta) * Decimal('0.95')
                    else:
                        precio_por_caja = cantidad_por_caja * precio_venta
            except:
                precio_por_caja = Decimal('0')

            # ============================================
            # 13. CÓDIGO DE BARRAS
            # ============================================
            codigo_barras_raw = row.get('Codigo de barra')
            codigo_barras = limpiar_valor_texto(codigo_barras_raw)

            # ============================================
            # 14. PREPARAR DATOS
            # ============================================
            datos = {
                'codigo': str(codigo_raw).strip(),
                'codigo_barras': codigo_barras,
                'categoria': categoria,
                'nombre_comercial': nombre_comercial,
                'principio_activo': principio_activo,
                'forma_farmaceutica': forma_farmaceutica,
                'registro_sanitario': registro_sanitario,
                'cantidad_por_caja': cantidad_por_caja,
                'lote': lote,
                'fecha_vencimiento': fecha_vencimiento,
                'fabricante': None,
                'proveedor': None,
                'stock_actual': max(0, stock_actual),
                'stock_minimo': 10,
                'precio_compra': precio_compra,
                'precio_venta': precio_venta,
                'precio_por_caja': precio_por_caja,
                'activo': True,
                'creado_por': usuario,
            }

            # ============================================
            # 15. GUARDAR
            # ============================================
            medicamento, created = Medicamento.objects.update_or_create(
                codigo=datos['codigo'],
                defaults=datos
            )

            if created:
                stats['creados'] += 1
                print(f"✅ [{stats['creados']}] CREADO: {medicamento.nombre_comercial}")
            else:
                stats['actualizados'] += 1
                print(f"🔄 [{stats['actualizados']}] ACTUALIZADO: {medicamento.nombre_comercial}")

        except Exception as e:
            stats['errores'] += 1
            print(f"❌ ERROR en fila {index+2}: {str(e)}")
            import traceback
            traceback.print_exc()

    # ============================================
    # RESUMEN FINAL
    # ============================================
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL")
    print("="*60)
    print(f"📦 Total filas procesadas: {len(df)}")
    print(f"✅ Creados: {stats['creados']}")
    print(f"🔄 Actualizados: {stats['actualizados']}")
    print(f"❌ Errores: {stats['errores']}")
    print(f"🏷️  Categorías creadas: {stats['categorias_creadas']}")
    print(f"📋 Con Registro Sanitario: {stats['con_registro']}")
    print(f"❌ Sin Registro Sanitario: {stats['sin_registro']}")
    print(f"⚠️  Sin nombre comercial: {stats['sin_nombre']}")

if __name__ == "__main__":
    excel_path = "/home/luis/policlinico/medicamentos_importar.xlsx"
    importar_medicamentos(excel_path)
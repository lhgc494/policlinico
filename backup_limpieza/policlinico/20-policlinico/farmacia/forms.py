from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
import re

from .models import (
    Medicamento,
    Categoria,
    Presentacion,
    Proveedor
)

# ==============================================
# FORMULARIOS PARA MEDICAMENTOS
# ==============================================
class MedicamentoForm(forms.ModelForm):
    # Campo código con validación
    codigo = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: MED-001'
        }),
        help_text='Código único del medicamento',
        error_messages={
            'required': 'El código es obligatorio'
        }
    )

    # Campo código de barras - MODIFICADO PARA PERMITIR VACÍO
    codigo_barras = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 123456789012'
        }),
        help_text='Código de barras (opcional - dejar vacío si no tiene)'
    )

    # Campo nombre comercial
    nombre_comercial = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Paracetamol 500mg'
        }),
        error_messages={
            'required': 'El nombre comercial es obligatorio'
        }
    )

    # Campo nombre genérico
    nombre_generico = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Acetaminofén'
        }),
        help_text='Nombre genérico (opcional)'
    )

    # Campo principio activo
    principio_activo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Paracetamol'
        }),
        error_messages={
            'required': 'El principio activo es obligatorio'
        }
    )

    # Campo concentración
    concentracion = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 500mg'
        }),
        error_messages={
            'required': 'La concentración es obligatoria'
        }
    )

    # Campo forma farmacéutica
    forma_farmaceutica = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Tableta, Cápsula, Jarabe'
        }),
        help_text='Forma farmacéutica (opcional)'
    )

    # Campo categoría
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activa=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label="Seleccione una categoría"
    )

    # Campo presentación
    presentacion = forms.ModelChoiceField(
        queryset=Presentacion.objects.filter(activa=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        empty_label="Seleccione una presentación"
    )

    # Campo stock_minimo (SÍ se puede editar)
    stock_minimo = forms.IntegerField(
        min_value=0,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1'
        }),
        help_text='Cantidad mínima para alerta de stock bajo'
    )

    # Campo stock_maximo (SÍ se puede editar)
    stock_maximo = forms.IntegerField(
        min_value=1,
        initial=1000,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1',
            'placeholder': 'Ej: 500, 1000, 5000'
        }),
        help_text='Cantidad máxima recomendada (puede ser cualquier número positivo)'
    )

    # Campos de precios
    precio_compra = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        help_text='Precio unitario de compra'
    )

    precio_venta = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        help_text='Precio unitario de venta al público'
    )

    precio_venta_mayorista = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        help_text='Precio para ventas al por mayor (opcional)'
    )

    # Campos de lote
    lote = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: LOTE-2024-001'
        }),
        help_text='Número de lote (opcional)'
    )

    registro_sanitario = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: RS-12345-2024'
        }),
        help_text='Registro sanitario (opcional)'
    )

    fecha_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Fecha de vencimiento (opcional)'
    )

    fabricante = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Laboratorio XYZ S.A.'
        }),
        help_text='Fabricante o laboratorio (opcional)'
    )

    # Campo proveedor
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Seleccione un proveedor"
    )

    # Campos de descripción
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción detallada del medicamento...'
        }),
        help_text='Descripción (opcional)'
    )

    indicaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Indicaciones médicas...'
        }),
        help_text='Indicaciones (opcional)'
    )

    contraindicaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Contraindicaciones y precauciones...'
        }),
        help_text='Contraindicaciones (opcional)'
    )

    condiciones_almacenamiento = forms.CharField(
        required=False,
        initial='Ambiente fresco y seco',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Ambiente fresco y seco'
        }),
        help_text='Condiciones de almacenamiento (opcional)'
    )

    # Campos de control
    requiere_receta = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='¿Requiere receta médica para su venta?'
    )

    controlado = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='¿Es un medicamento controlado?'
    )

    refrigerado = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='¿Requiere refrigeración?'
    )

    # Campo activo
    activo = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='¿Activo en el sistema?'
    )

    class Meta:
        model = Medicamento
        # EXCLUIR stock_actual (no se edita directamente) y propiedades calculadas
        exclude = [
            'stock_actual',              # ¡NO se edita directamente! Se ajusta por movimientos
            'valor_inventario',
            'dias_vencimiento',
            'vencido',
            'proximo_vencer',
            'bajo_stock',
            'margen_ganancia',
            'estado_stock',
            'porcentaje_stock',
            'nombre_display',
            'valor_venta_inventario',
            'fecha_creacion',
            'fecha_actualizacion',
            'creado_por'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # IMPORTANTE: Si estamos editando un medicamento existente
        if self.instance and self.instance.pk:
            # Campo informativo de stock actual (solo lectura)
            self.fields['stock_info'] = forms.CharField(
                required=False,
                initial=f'Stock actual: {self.instance.stock_actual} unidades',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'readonly': 'readonly',
                    'style': 'background-color: #f8f9fa; font-weight: bold;'
                }),
                help_text='⚠️ El stock se ajusta mediante "Movimientos de Inventario"',
                label='Stock Actual (información)'
            )
            
            # Reordenar campos para que stock_info aparezca primero
            field_order = list(self.fields.keys())
            if 'stock_info' in field_order:
                field_order.remove('stock_info')
            field_order.insert(5, 'stock_info')  # Después de los campos básicos
            self.order_fields(field_order)
            
            # Convertir código de barras vacío a None
            if self.instance.codigo_barras == '':
                self.instance.codigo_barras = None

            # Si stock_maximo es None, establecer valor por defecto
            if self.instance.stock_maximo is None:
                self.fields['stock_maximo'].initial = 1000
            else:
                # Mostrar el valor actual
                self.fields['stock_maximo'].initial = self.instance.stock_maximo

        # Configurar placeholders específicos para edición
        if self.instance and self.instance.pk:
            # Si estamos editando, hacer código de barras no requerido explícitamente
            self.fields['codigo_barras'].required = False
            self.fields['codigo_barras'].help_text = 'Código de barras (dejar vacío para eliminar)'

        # Mostrar que stock_maximo puede ser grande
        if self.instance and self.instance.pk and self.instance.stock_maximo:
            if self.instance.stock_maximo > 1000:
                self.fields['stock_maximo'].help_text = f'Stock máximo actual: {self.instance.stock_maximo} (puede editar)'

    def clean_codigo(self):
        """Validación del código único"""
        codigo = self.cleaned_data.get('codigo')

        if not codigo:
            raise ValidationError('El código es obligatorio')

        # Validar que no exista otro medicamento con el mismo código
        if self.instance and self.instance.pk:
            # Estamos editando
            existe = Medicamento.objects.filter(
                codigo=codigo
            ).exclude(pk=self.instance.pk).exists()
        else:
            # Estamos creando
            existe = Medicamento.objects.filter(codigo=codigo).exists()

        if existe:
            raise ValidationError('Ya existe un medicamento con este código')

        return codigo

    def clean_codigo_barras(self):
        """Validación del código de barras - CORREGIDO PARA PERMITIR VACÍO"""
        codigo_barras = self.cleaned_data.get('codigo_barras', '').strip()

        # Si está vacío, retornar None (no cadena vacía)
        if codigo_barras == '':
            return None

        # Solo validar unicidad si hay un valor
        if codigo_barras:
            if self.instance and self.instance.pk:
                # Estamos editando - excluir el medicamento actual
                existe = Medicamento.objects.filter(
                    codigo_barras=codigo_barras
                ).exclude(pk=self.instance.pk).exists()
            else:
                # Estamos creando
                existe = Medicamento.objects.filter(codigo_barras=codigo_barras).exists()

            if existe:
                raise ValidationError('Ya existe un medicamento con este código de barras')

        return codigo_barras

    def clean_stock_minimo(self):
        """Validación del stock mínimo"""
        stock_minimo = self.cleaned_data.get('stock_minimo', 0)
        stock_maximo = self.cleaned_data.get('stock_maximo', 1000)  # Default 1000

        if stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')

        if stock_maximo and stock_minimo > stock_maximo:
            raise ValidationError(
                f'El stock mínimo ({stock_minimo}) no puede ser mayor '
                f'al stock máximo ({stock_maximo})'
            )

        return stock_minimo

    def clean_stock_maximo(self):
        """Validación del stock máximo - PERMITE CUALQUIER VALOR > 0"""
        stock_maximo = self.cleaned_data.get('stock_maximo')
        
        # Si no se proporcionó valor, usar el valor del modelo o 1000
        if stock_maximo is None:
            if self.instance and self.instance.stock_maximo:
                return self.instance.stock_maximo
            return 1000  # Valor por defecto alto

        if stock_maximo <= 0:
            raise ValidationError('El stock máximo debe ser mayor a 0')

        # Puede ser cualquier número positivo
        try:
            return int(stock_maximo)
        except (ValueError, TypeError):
            raise ValidationError('El stock máximo debe ser un número válido')

    def clean_precio_venta(self):
        """Validación del precio de venta"""
        precio_venta = self.cleaned_data.get('precio_venta', 0)
        precio_compra = self.cleaned_data.get('precio_compra', 0)

        if precio_venta < 0:
            raise ValidationError('El precio de venta no puede ser negativo')

        if precio_compra and precio_venta < precio_compra:
            raise ValidationError(
                f'El precio de venta (S/ {precio_venta:.2f}) no puede ser menor '
                f'al precio de compra (S/ {precio_compra:.2f})'
            )

        return precio_venta

    def clean_precio_venta_mayorista(self):
        """Validación del precio de venta mayorista"""
        precio_mayorista = self.cleaned_data.get('precio_venta_mayorista', 0)
        precio_compra = self.cleaned_data.get('precio_compra', 0)
        precio_venta = self.cleaned_data.get('precio_venta', 0)

        if precio_mayorista and precio_mayorista < 0:
            raise ValidationError('El precio mayorista no puede ser negativo')

        if precio_mayorista and precio_compra and precio_mayorista < precio_compra:
            raise ValidationError(
                f'El precio mayorista (S/ {precio_mayorista:.2f}) no puede ser menor '
                f'al precio de compra (S/ {precio_compra:.2f})'
            )

        if precio_mayorista and precio_venta and precio_mayorista > precio_venta:
            raise ValidationError(
                f'El precio mayorista (S/ {precio_mayorista:.2f}) no puede ser mayor '
                f'al precio de venta al público (S/ {precio_venta:.2f})'
            )

        return precio_mayorista

    def clean_fecha_vencimiento(self):
        """Validación de fecha de vencimiento"""
        fecha_vencimiento = self.cleaned_data.get('fecha_vencimiento')

        if fecha_vencimiento:
            hoy = date.today()

            if fecha_vencimiento < hoy:
                raise ValidationError('La fecha de vencimiento no puede ser pasada')

        return fecha_vencimiento

    def clean(self):
        """Validaciones cruzadas entre campos - SIMPLIFICADA"""
        cleaned_data = super().clean()

        # Validación simple entre stock_minimo y stock_maximo
        stock_minimo = cleaned_data.get('stock_minimo', 0)
        stock_maximo = cleaned_data.get('stock_maximo', 1000)
        
        if stock_maximo and stock_minimo > stock_maximo:
            self.add_error(
                'stock_minimo',
                f'El stock mínimo ({stock_minimo}) no puede ser mayor '
                f'al stock máximo ({stock_maximo})'
            )
        
        # Asegurar que stock_maximo tenga un valor razonable si está vacío
        if 'stock_maximo' in cleaned_data and cleaned_data['stock_maximo'] is None:
            cleaned_data['stock_maximo'] = 1000
            
        # Asegurar que código de barras vacío sea None, no cadena vacía
        if 'codigo_barras' in cleaned_data and cleaned_data['codigo_barras'] == '':
            cleaned_data['codigo_barras'] = None

        return cleaned_data

# ==============================================
# FORMULARIOS PARA PROVEEDORES
# ==============================================

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if ruc:
            if not ruc.isdigit() or len(ruc) != 11:
                raise ValidationError('El RUC debe tener 11 dígitos numéricos.')
        return ruc

# ==============================================
# FORMULARIOS PARA CATEGORÍAS
# ==============================================

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

# ==============================================
# FORMULARIOS PARA PRESENTACIONES
# ==============================================

class PresentacionForm(forms.ModelForm):
    class Meta:
        model = Presentacion
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

# ==============================================
# FORMULARIOS PARA VENTAS (SI LOS NECESITAS MÁS ADELANTE)
# ==============================================

# Si necesitas formularios para ventas, los puedes agregar después
# cuando tengas el sistema funcionando

# class VentaForm(forms.ModelForm):
#     class Meta:
#         model = Venta  # Este modelo SÍ existe
#         fields = ['metodo_pago', 'observaciones']
#         widgets = {
#             'observaciones': forms.Textarea(attrs={'rows': 2}),
#         }

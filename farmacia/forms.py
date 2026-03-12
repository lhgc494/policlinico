# /home/luis/policlinico/farmacia/forms.py

from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .models import (
    Medicamento,
    Categoria,
    Proveedor
)

# ==============================================
# FORMULARIOS PARA MEDICAMENTOS
# ==============================================

class MedicamentoForm(forms.ModelForm):
    """Formulario para crear/editar medicamentos"""

    class Meta:
        model = Medicamento
        fields = [
            'codigo',
            'codigo_barras',
            'categoria',
            'nombre_comercial',
            'principio_activo',
            'forma_farmaceutica',
            'fabricante',
            'proveedor',
            #'stock_actual',
            'stock_minimo',
            'cantidad_por_caja',
            'precio_compra',
            'precio_venta',
            'precio_por_caja',
            'lote',
            'registro_sanitario',
            'fecha_vencimiento',
            'activo',
        ]
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: MED001'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Amoxidal 500mg'}),
            'principio_activo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Amoxicilina'}),
            'forma_farmaceutica': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tableta, Cápsula, Jarabe'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Roemmers'}),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '10'}),
            'cantidad_por_caja': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'precio_por_caja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: L2025-001'}),
            'registro_sanitario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: EE-12345'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'codigo': 'Código',
            'codigo_barras': 'Código de Barras',
            'categoria': 'Categoría/Grupo',
            'nombre_comercial': 'Nombre Comercial',
            'principio_activo': 'Principio Activo',
            'forma_farmaceutica': 'Forma Farmacéutica',
            'fabricante': 'Fabricante/Laboratorio',
            'proveedor': 'Proveedor',
            'stock_actual': 'Stock Actual',
            'stock_minimo': 'Stock Mínimo',
            'cantidad_por_caja': 'Cantidad por Caja',
            'precio_compra': 'Precio de Compra',
            'precio_venta': 'Precio de Venta',
            'precio_por_caja': 'Precio por Caja',
            'lote': 'Lote',
            'registro_sanitario': 'Registro Sanitario',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'activo': 'Activo',
        }
        help_texts = {
            'codigo': 'Código único del medicamento',
            'stock_minimo': 'Cantidad mínima para alerta de stock bajo',
            'precio_por_caja': 'Precio de venta por caja completa (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos requeridos
        self.fields['codigo'].required = True
        self.fields['nombre_comercial'].required = True
        self.fields['principio_activo'].required = True
        #self.fields['stock_actual'].required = True
        self.fields['stock_minimo'].required = True
        self.fields['precio_compra'].required = True
        self.fields['precio_venta'].required = True

        # Si es edición y precio_por_caja vacío, calcularlo
        if self.instance and self.instance.pk:
            if not self.instance.precio_por_caja and self.instance.cantidad_por_caja and self.instance.cantidad_por_caja > 1:
                self.instance.precio_por_caja = (self.instance.cantidad_por_caja * self.instance.precio_venta) * 0.95

    def clean_codigo(self):
        """Validar código único"""
        codigo = self.cleaned_data.get('codigo')
        if not codigo:
            raise ValidationError('El código es obligatorio')

        queryset = Medicamento.objects.filter(codigo=codigo)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError('Ya existe un medicamento con este código')
        return codigo

    def clean_codigo_barras(self):
        """Validar código de barras - convertir vacío a None"""
        codigo_barras = self.cleaned_data.get('codigo_barras')
        
        # Si es None o cadena vacía, retornar None
        if not codigo_barras:
            return None
        
        # Si es string, limpiar espacios
        if isinstance(codigo_barras, str):
            codigo_barras = codigo_barras.strip()
            if not codigo_barras:
                return None
        
        # Validar unicidad
        queryset = Medicamento.objects.filter(codigo_barras=codigo_barras)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError('Ya existe un medicamento con este código de barras')
        
        return codigo_barras

    def clean_stock_actual(self):
        """Validar stock actual no negativo"""
        stock = self.cleaned_data.get('stock_actual')
        if stock is not None and stock < 0:
            raise ValidationError('El stock actual no puede ser negativo')
        return stock

    def clean_stock_minimo(self):
        """Validar stock mínimo no negativo"""
        stock_min = self.cleaned_data.get('stock_minimo')
        if stock_min is not None and stock_min < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')
        return stock_min

    def clean_precio_venta(self):
        """Validar que precio de venta sea mayor o igual al de compra"""
        precio_venta = self.cleaned_data.get('precio_venta')
        precio_compra = self.cleaned_data.get('precio_compra')

        if precio_venta and precio_compra and precio_venta < precio_compra:
            raise ValidationError(
                f'El precio de venta (S/ {precio_venta:.2f}) no puede ser '
                f'menor al precio de compra (S/ {precio_compra:.2f})'
            )
        return precio_venta

    def clean_fecha_vencimiento(self):
        """Validar fecha de vencimiento no pasada"""
        fecha = self.cleaned_data.get('fecha_vencimiento')
        if fecha and fecha < date.today():
            raise ValidationError('La fecha de vencimiento no puede ser en el pasado')
        return fecha


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

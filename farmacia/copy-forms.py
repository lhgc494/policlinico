from django import forms
from django.core.exceptions import ValidationError
from .models import Medicamento, Categoria, Presentacion, Proveedor
import re
from datetime import date
from django import forms
from .models import Proveedor, Categoria, Presentacion
from .models import VentaDirecta, DetalleVentaDirecta
## venta directa ######
class VentaDirectaForm(forms.ModelForm):
    class Meta:
        model = VentaDirecta
        fields = ['paciente', 'cliente_externo', 'dni', 'descuento', 'metodo_pago', 'observaciones']
        widgets = {
            'cliente_externo': forms.TextInput(attrs={'placeholder': 'Nombre del cliente si no es paciente'}),
            'dni': forms.TextInput(attrs={'placeholder': 'DNI opcional'}),
            'descuento': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente')
        cliente_externo = cleaned_data.get('cliente_externo')
        
        # Validar que se ingrese paciente o cliente externo
        if not paciente and not cliente_externo:
            raise forms.ValidationError("Debe seleccionar un paciente o ingresar un cliente externo.")
        
        return cleaned_data


class DetalleVentaForm(forms.ModelForm):
    medicamento_codigo = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Código o nombre',
            'id': 'buscar-medicamento'
        }),
        required=True
    )
    
    class Meta:
        model = DetalleVentaDirecta
        fields = ['medicamento_codigo', 'cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1}),
        }


#######################
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

class PresentacionForm(forms.ModelForm):
    class Meta:
        model = Presentacion
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

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
    
    # Campo código de barras
    codigo_barras = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 123456789012'
        }),
        help_text='Código de barras (opcional)'
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
    
    # Campos de stock
    stock_actual = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1'
        }),
        help_text='Cantidad actual en inventario'
    )
    
    stock_minimo = forms.IntegerField(
        min_value=0,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1'
        }),
        help_text='Cantidad mínima para alerta de stock bajo'
    )
    
    stock_maximo = forms.IntegerField(
        min_value=1,
        initial=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '1'
        }),
        help_text='Cantidad máxima recomendada en inventario'
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
        fields = [
            # Información básica
            'codigo', 'codigo_barras', 'nombre_comercial', 'nombre_generico',
            'principio_activo', 'concentracion', 'forma_farmaceutica',
            
            # Clasificación
            'categoria', 'presentacion',
            
            # Stock y precios
            'stock_actual', 'stock_minimo', 'stock_maximo',
            'precio_compra', 'precio_venta', 'precio_venta_mayorista',
            
            # Información de lote
            'lote', 'registro_sanitario', 'fecha_vencimiento',
            'fabricante', 'proveedor',
            
            # Información adicional
            'descripcion', 'indicaciones', 'contraindicaciones',
            'condiciones_almacenamiento',
            
            # Control de estado
            'requiere_receta', 'controlado', 'refrigerado', 'activo'
        ]
    
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
        """Validación del código de barras"""
        codigo_barras = self.cleaned_data.get('codigo_barras', '').strip()
        
        if codigo_barras:
            # Validar que no exista otro medicamento con el mismo código de barras
            if self.instance and self.instance.pk:
                existe = Medicamento.objects.filter(
                    codigo_barras=codigo_barras
                ).exclude(pk=self.instance.pk).exists()
            else:
                existe = Medicamento.objects.filter(codigo_barras=codigo_barras).exists()
            
            if existe:
                raise ValidationError('Ya existe un medicamento con este código de barras')
        
        return codigo_barras
    
    def clean_stock_minimo(self):
        """Validación del stock mínimo"""
        stock_minimo = self.cleaned_data.get('stock_minimo', 0)
        stock_maximo = self.cleaned_data.get('stock_maximo', 0)
        
        if stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')
        
        if stock_maximo and stock_minimo > stock_maximo:
            raise ValidationError(
                f'El stock mínimo ({stock_minimo}) no puede ser mayor '
                f'al stock máximo ({stock_maximo})'
            )
        
        return stock_minimo
    
    def clean_stock_maximo(self):
        """Validación del stock máximo"""
        stock_maximo = self.cleaned_data.get('stock_maximo', 0)
        
        if stock_maximo <= 0:
            raise ValidationError('El stock máximo debe ser mayor a 0')
        
        return stock_maximo
    
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
        """Validaciones cruzadas entre campos"""
        cleaned_data = super().clean()
        
        # Validar que stock actual no sea mayor que stock máximo
        stock_actual = cleaned_data.get('stock_actual', 0)
        stock_maximo = cleaned_data.get('stock_maximo', 0)
        
        if stock_maximo and stock_actual > stock_maximo:
            self.add_error(
                'stock_actual',
                f'El stock actual ({stock_actual}) no puede ser mayor '
                f'al stock máximo ({stock_maximo})'
            )
        
        return cleaned_data

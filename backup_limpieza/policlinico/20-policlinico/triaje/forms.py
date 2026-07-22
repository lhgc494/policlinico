from django import forms
from .models import Triaje
from django.core.exceptions import ValidationError
import re


def validar_presion_form(value):
    """
    Valida presión arterial en formato 120/80 para el formulario
    """
    if not re.match(r'^\d{2,3}/\d{2,3}$', value):
        raise ValidationError('Formato inválido. Use el formato 120/80')
    return value


class TriajeForm(forms.ModelForm):
    # Campos con validaciones adicionales
    peso = forms.DecimalField(
        label='Peso (kg)',
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Ej: 65.5'
        })
    )

    talla = forms.IntegerField(
        label='Talla (cm)',
        min_value=0,
        max_value=250,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 170'
        })
    )

    temperatura = forms.DecimalField(
        label='Temperatura (°C)',
        min_value=20,
        max_value=45,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Ej: 36.5'
        })
    )

    presion = forms.CharField(
        label='Presión Arterial',
        validators=[validar_presion_form],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 120/80'
        }),
        help_text='Formato: 120/80'
    )

    frecuencia_cardiaca = forms.IntegerField(
        label='Frecuencia Cardíaca (lpm)',
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 72'
        })
    )

    saturacion = forms.IntegerField(
        label='Saturación de Oxígeno (%)',
        min_value=50,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 98'
        })
    )

    class Meta:
        model = Triaje
        fields = [
            'peso',
            'talla',
            'temperatura',
            'presion',
            'frecuencia_cardiaca',
            'saturacion',
        ]

    def clean(self):
        cleaned_data = super().clean()

        # Validar que todos los campos estén presentes
        campos_requeridos = ['peso', 'talla', 'temperatura', 'presion',
                           'frecuencia_cardiaca', 'saturacion']

        for campo in campos_requeridos:
            if campo not in cleaned_data or cleaned_data[campo] is None:
                self.add_error(campo, 'Este campo es requerido')

        # Validación adicional de saturación
        saturacion = cleaned_data.get('saturacion')
        if saturacion and not (50 <= saturacion <= 100):
            self.add_error('saturacion', 'La saturación debe estar entre 50 y 100%')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Marcar automáticamente como completo si todos los campos están llenos
        campos_llenos = all([
            instance.peso is not None,
            instance.talla is not None,
            instance.temperatura is not None,
            instance.presion,
            instance.frecuencia_cardiaca is not None,
            instance.saturacion is not None,
        ])

        if campos_llenos:
            instance.estado = Triaje.EstadoTriaje.COMPLETO

        if commit:
            instance.save()

        return instance

#######
class EditarTriajeForm(forms.Form):
    """
    Formulario para editar triajes - NO hereda de ModelForm para evitar validaciones
    """
    peso = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Ej: 65.5'
        })
    )
    
    talla = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=250,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 170'
        })
    )
    
    temperatura = forms.DecimalField(
        required=False,
        min_value=20,
        max_value=45,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Ej: 36.5'
        })
    )
    
    presion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 120/80'
        })
    )
    
    frecuencia_cardiaca = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 72'
        })
    )
    
    saturacion = forms.IntegerField(
        required=False,
        min_value=50,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 98'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # Si hay una instancia, establecer valores iniciales
        if self.instance:
            initial_data = {}
            for field in self.fields:
                value = getattr(self.instance, field, None)
                initial_data[field] = value
            self.initial = initial_data
    
    def clean_presion(self):
        presion = self.cleaned_data.get('presion')
        if presion and presion.strip():  # Solo validar si hay valor
            if not re.match(r'^\d{2,3}/\d{2,3}$', presion):
                raise ValidationError('Formato inválido. Use el formato 120/80')
        return presion
    
    def clean_saturacion(self):
        saturacion = self.cleaned_data.get('saturacion')
        if saturacion is not None:
            if not (50 <= saturacion <= 100):
                raise ValidationError('La saturación debe estar entre 50 y 100%')
        return saturacion
    
    def save(self, triaje_id):
        """Guarda los datos directamente en la base de datos sin validaciones del modelo"""
        cleaned_data = self.cleaned_data
        
        # Filtrar solo los campos que tienen valores
        update_data = {}
        for field in ['peso', 'talla', 'temperatura', 'presion', 
                     'frecuencia_cardiaca', 'saturacion']:
            if field in cleaned_data and cleaned_data[field] is not None:
                update_data[field] = cleaned_data[field]
        
        if update_data:
            # Usar update() para evitar validaciones del modelo
            from django.db import connection
            with connection.cursor() as cursor:
                set_clauses = []
                values = []
                for field, value in update_data.items():
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
                
                values.append(triaje_id)
                query = f"""
                    UPDATE triaje_triaje 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                cursor.execute(query, values)
        
        return True

############

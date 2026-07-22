from django import forms
from django.core.exceptions import ValidationError
from .models import Paciente
import re
from datetime import date

class PacienteForm(forms.ModelForm):
    # Campo DNI con validación personalizada
    dni = forms.CharField(
        max_length=8,
        min_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 87654321'
        }),
        help_text='Debe tener exactamente 8 dígitos',
        error_messages={
            'required': 'El DNI es obligatorio',
            'min_length': 'El DNI debe tener 8 dígitos',
            'max_length': 'El DNI debe tener 8 dígitos',
        }
    )
    
    # Campo nombres
    nombres = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Carlos'
        }),
        error_messages={
            'required': 'Los nombres son obligatorios'
        }
    )
    
    # Campo apellidos
    apellidos = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Pérez López'
        }),
        error_messages={
            'required': 'Los apellidos son obligatorios'
        }
    )
    
    # Campo fecha de nacimiento
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        error_messages={
            'required': 'La fecha de nacimiento es obligatoria',
            'invalid': 'Ingrese una fecha válida (dd/mm/aaaa)'
        }
    )
    
    # Campo teléfono (opcional pero con validación)
    telefono = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 987654321'
        }),
        help_text='Opcional - 9 dígitos'
    )
    
    # Campo dirección (opcional)
    direccion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Av. Principal 123'
        })
    )

    # Campo activo
   # activo = forms.BooleanField(
    #    required=False,
     #   initial=True,
      #  widget=forms.CheckboxInput(attrs={
       #     'class': 'form-check-input'
       # }),
       # help_text='Desmarcar si el paciente ya no es atendido en el policlínico'
   # )

    class Meta:
        model = Paciente
        fields = [
            'dni',
            'nombres',
            'apellidos',
            'fecha_nacimiento',
            'telefono',
            'direccion',
           # 'activo'
        ]

    def clean_dni(self):
        """Validación personalizada para DNI"""
        dni = self.cleaned_data.get('dni')
        
        # 1. Validar que no esté vacío
        if not dni:
            raise ValidationError('El DNI es obligatorio')
        
        # 2. Validar que sean solo números
        if not dni.isdigit():
            raise ValidationError('El DNI debe contener solo números (0-9)')
        
        # 3. Validar longitud exacta de 8 dígitos
        if len(dni) != 8:
            raise ValidationError('El DNI debe tener exactamente 8 dígitos')
        
        # 4. Validar que no exista otro paciente con el mismo DNI
        # (excepto si estamos editando este mismo paciente)
        if self.instance and self.instance.pk:
            # Estamos editando, excluir el paciente actual
            paciente_existente = Paciente.objects.filter(dni=dni).exclude(pk=self.instance.pk)
        else:
            # Estamos creando nuevo
            paciente_existente = Paciente.objects.filter(dni=dni)
        
        if paciente_existente.exists():
            paciente = paciente_existente.first()
            raise ValidationError(
                f'Ya existe un paciente registrado con este DNI: '
                f'{paciente.nombres} {paciente.apellidos} (DNI: {paciente.dni})'
            )
        
        return dni

    def clean_telefono(self):
        """Validación personalizada para teléfono"""
        telefono = self.cleaned_data.get('telefono', '')
        
        if telefono:  # Solo validar si se ingresó un teléfono
            # Remover espacios, guiones, paréntesis
            telefono = re.sub(r'[\s\-\(\)]+', '', telefono)
            
            # Validar que sean solo números
            if not telefono.isdigit():
                raise ValidationError('El teléfono debe contener solo números')
            
            # Validar longitud (9 dígitos para Perú)
            if len(telefono) != 9:
                raise ValidationError('El teléfono debe tener 9 dígitos')
            
            return telefono
        
        return telefono  # Retornar vacío si no hay teléfono

    def clean_fecha_nacimiento(self):
        """Validación personalizada para fecha de nacimiento"""
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento:
            hoy = date.today()
            
            # Validar que no sea fecha futura
            if fecha_nacimiento > hoy:
                raise ValidationError('La fecha de nacimiento no puede ser futura')
            
            # Calcular edad
            edad = hoy.year - fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
            )
            
            # Validar que sea una edad razonable (opcional)
            if edad < 0:
                raise ValidationError('Edad no válida')
            elif edad > 120:
                raise ValidationError('Edad no válida (máximo 120 años)')
            
            # Opcional: Validar que sea mayor de 18 años
            # if edad < 18:
            #     raise ValidationError('El paciente debe ser mayor de edad (18 años)')
        
        return fecha_nacimiento

    def clean(self):
        """Validaciones cruzadas entre campos"""
        cleaned_data = super().clean()
        
        # Aquí puedes agregar validaciones que involucren múltiples campos
        
        return cleaned_data

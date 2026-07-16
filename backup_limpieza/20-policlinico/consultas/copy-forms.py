from django import forms
from .models import Consulta, Receta
from doctores.models import Doctor
from .models import OrdenExamen

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ['tarifa', 'doctor']
        widgets = {
            'tarifa': forms.Select(attrs={
                'class': 'form-control'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicialmente, mostrar todos los doctores activos
        self.fields['doctor'].queryset = Doctor.objects.filter(activo=True)
        self.fields['doctor'].label = 'Médico asignado'
        self.fields['doctor'].required = True

        # Ordenar doctores por apellido
        self.fields['doctor'].queryset = self.fields['doctor'].queryset.order_by('apellidos', 'nombres')


class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamento', 'dosis', 'frecuencia', 'duracion', 'indicaciones']
        widgets = {
            'medicamento': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_medicamento',
                'placeholder': 'Escriba el nombre del medicamento...',
                'autocomplete': 'off'
            }),
            'dosis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1 tableta'
            }),
            'frecuencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cada 8 horas'
            }),
            'duracion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 7 días'
            }),
            'indicaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ej: Tomar después de alimentos'
            }),
        }
        labels = {
            'medicamento': 'Medicamento *',
            'dosis': 'Dosis *',
            'frecuencia': 'Frecuencia *',
            'duracion': 'Duración *',
            'indicaciones': 'Indicaciones'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicamento'].required = True
        self.fields['indicaciones'].required = False


class OrdenExamenForm(forms.ModelForm):
    class Meta:
        model = OrdenExamen
        # SOLO incluir campos que realmente existen
        fields = ['tipo_examen', 'examen_especifico']  # ← Sin 'notas'
        widgets = {
            'tipo_examen': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo_examen'
            }),
            'examen_especifico': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Hemograma completo, Glucosa en ayunas...'
            }),
        }
        labels = {
            'tipo_examen': 'Tipo de Examen *',
            'examen_especifico': 'Examen Específico *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['examen_especifico'].required = True

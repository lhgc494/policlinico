from django import forms
from .models import Consulta, Receta, OrdenExamen
from doctores.models import Doctor

# Lista de exámenes que ofrece la clínica (INVENTADOS - REEMPLAZAR LUEGO)
EXAMENES_LABORATORIO = [
    ('HEMOGRAMA', 'Hemograma completo'),
    ('GLUCOSA', 'Glucosa en ayunas'),
    ('COLESTEROL', 'Colesterol total'),
    ('TRIGLICERIDOS', 'Triglicéridos'),
    ('UREA', 'Urea'),
    ('CREATININA', 'Creatinina'),
    ('TGO', 'TGO (AST)'),
    ('TGP', 'TGP (ALT)'),
    ('BILIRRUBINA', 'Bilirrubina total'),
    ('PROTEINAS', 'Proteínas totales'),
    ('OTRO', 'Otro (especificar)'),
]

ECOGRAFIAS = [
    ('ABDOMINAL', 'Ecografía abdominal completa'),
    ('PELVICA', 'Ecografía pélvica'),
    ('TIROIDES', 'Ecografía de tiroides'),
    ('MAMA', 'Ecografía de mama'),
    ('RENAL', 'Ecografía renal'),
    ('VESICAL', 'Ecografía vesical'),
    ('OBSTETRICA', 'Ecografía obstétrica'),
    ('PROSTATICA', 'Ecografía prostática'),
    ('TESTICULAR', 'Ecografía testicular'),
    ('PARTES_BLANDAS', 'Ecografía de partes blandas'),
    ('OTRO', 'Otro (especificar)'),
]

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
    # Campo personalizado para tipo de examen (solo 3 opciones)
    tipo_examen = forms.ChoiceField(
        choices=[
            ('LABORATORIO', 'Laboratorio'),
            ('ECOGRAFIA', 'Ecografía'),
            ('OTRO', 'Otro'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_tipo_examen',
            'onchange': 'actualizarExamenes()'
        }),
        label='Tipo de Examen *'
    )
    
    # Campo dinámico para examen específico (se llena según tipo)
    examen_especifico = forms.ChoiceField(
        choices=[],  # Se llena dinámicamente
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_examen_especifico'
        }),
        label='Examen Específico *',
        required=True
    )
    
    # Campo para "Otros" (solo visible cuando tipo = OTRO)
    examen_otro = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_examen_otro',
            'placeholder': 'Ej: Resonancia magnética, Tomografía...',
            'style': 'display: none;'
        }),
        label='Especifique el examen'
    )
    
    class Meta:
        model = OrdenExamen
        fields = ['tipo_examen', 'examen_especifico', 'indicaciones']
        widgets = {
            'indicaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Preparación especial o indicaciones...'
            }),
        }
        labels = {
            'indicaciones': 'Indicaciones (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remover campo "urgente" si existe (no se usa)
        if 'urgente' in self.fields:
            del self.fields['urgente']
        
        # Inicializar con exámenes de laboratorio por defecto
        self.fields['examen_especifico'].choices = EXAMENES_LABORATORIO
        
        # Si ya tiene un valor guardado, configurar según el tipo
        if self.instance and self.instance.pk:
            self.fields['tipo_examen'].initial = self.instance.tipo_examen
            
            if self.instance.tipo_examen == 'OTRO':
                # Para "Otros", usar el campo de texto
                self.fields['examen_otro'].initial = self.instance.examen_especifico
                self.fields['examen_otro'].widget.attrs['style'] = ''  # Mostrar
                self.fields['examen_especifico'].required = False
            elif self.instance.tipo_examen == 'ECOGRAFIA':
                # Para ecografías, cargar lista de ecografías
                self.fields['examen_especifico'].choices = ECOGRAFIAS
            else:
                # Para laboratorio, mantener lista de laboratorio
                self.fields['examen_especifico'].choices = EXAMENES_LABORATORIO
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_examen = cleaned_data.get('tipo_examen')
        examen_especifico = cleaned_data.get('examen_especifico')
        examen_otro = cleaned_data.get('examen_otro')
        
        # Validar que si es "OTRO", se haya especificado el examen
        if tipo_examen == 'OTRO':
            if not examen_otro or examen_otro.strip() == '':
                raise forms.ValidationError({
                    'examen_otro': 'Debe especificar el examen cuando selecciona "Otro".'
                })
            # Asignar el valor de examen_otro a examen_especifico
            cleaned_data['examen_especifico'] = examen_otro
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Si es "OTRO", usar el campo examen_otro como examen_especifico
        if self.cleaned_data.get('tipo_examen') == 'OTRO':
            instance.examen_especifico = self.cleaned_data.get('examen_otro', '')
        
        if commit:
            instance.save()
        
        return instance

################ ecografias
class EcografiaForm(forms.ModelForm):
    # Solo ecografías que ofrece la clínica
    ECOGRAFIAS_CLINICA = [
        ('ABDOMINAL', 'Ecografía Abdominal Completa'),
        ('PELVICA', 'Ecografía Pélvica'),
        ('TIROIDES', 'Ecografía de Tiroides'),
        ('MAMA', 'Ecografía de Mama'),
        ('RENAL', 'Ecografía Renal'),
        ('VESICAL', 'Ecografía Vesical'),
        ('OBSTETRICA', 'Ecografía Obstétrica'),
        ('PROSTATICA', 'Ecografía Prostática'),
        ('TESTICULAR', 'Ecografía Testicular'),
        ('PARTES_BLANDAS', 'Ecografía de Partes Blandas'),
    ]
    
    tipo_ecografia = forms.ChoiceField(
        choices=ECOGRAFIAS_CLINICA + [('OTRO', 'Otro (especificar)')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Ecografía *'
    )
    
    especificar_otro = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Especifique el tipo de ecografía...',
            'style': 'display: none;'
        }),
        label='Especificar'
    )
    
    indicaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Indicaciones especiales...'
        }),
        label='Indicaciones'
    )
    
    class Meta:
        model = OrdenExamen  # O crear modelo Ecografia si prefieres
        fields = ['tipo_ecografia', 'indicaciones']

#############################

# Formulario para imprimir (opcional, para botón de impresión)
class ImprimirRecetasForm(forms.Form):
    consulta_id = forms.IntegerField(widget=forms.HiddenInput())
    

class ImprimirExamenesForm(forms.Form):
    consulta_id = forms.IntegerField(widget=forms.HiddenInput())

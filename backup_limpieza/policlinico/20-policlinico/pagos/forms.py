from django import forms
from .models import OrdenPago


class RegistrarPagoForm(forms.ModelForm):
    class Meta:
        model = OrdenPago
        fields = ['metodo_pago']
        widgets = {
            'metodo_pago': forms.Select(
                attrs={'class': 'form-select'}
            )
        }

    def clean_metodo_pago(self):
        metodo = self.cleaned_data.get('metodo_pago')
        if not metodo:
            raise forms.ValidationError(
                'Debe seleccionar un método de pago.'
            )
        return metodo


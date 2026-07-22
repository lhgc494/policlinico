from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('dni', 'apellidos', 'nombres', 'telefono')
    search_fields = ('dni', 'nombres', 'apellidos')


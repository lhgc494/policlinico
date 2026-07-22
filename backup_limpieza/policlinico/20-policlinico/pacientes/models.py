from django.db import models
from datetime import date  # ← AGREGAR ESTO
from dateutil.relativedelta import relativedelta  # ← AGREGAR ESTO

class Paciente(models.Model):
    dni = models.CharField(max_length=8, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, verbose_name='¿Activo?',help_text='Indica si el paciente está activo en el sistema')

    @property
    def edad(self):
        """
        Calcula la edad en años a partir de la fecha de nacimiento
        """
        if self.fecha_nacimiento:
            hoy = date.today()
            return hoy.year - self.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    @property
    def edad_completa(self):
        """
        Calcula edad en años, meses y días
        """
        if self.fecha_nacimiento:
            hoy = date.today()
            diferencia = relativedelta(hoy, self.fecha_nacimiento)
            return f"{diferencia.years} años, {diferencia.months} meses"
        return "No registrada"

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

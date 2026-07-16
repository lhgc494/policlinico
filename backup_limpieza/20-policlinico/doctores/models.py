from django.db import models

# Create your models here.
from django.db import models

from django.db import models
from django.contrib.auth.models import User  # Agregar esto al inicio

class Especialidad(models.Model):
    """
    Especialidades médicas - Sincronizado con TarifaConsulta
    """
    ESPECIALIDADES = [
        ('GENERAL', 'Medicina General'),
        ('ECOGRAFIA', 'Ecografía'),
        ('PEDIATRIA', 'Pediatría'),
        ('PSICOLOGIA', 'Psicología'),
        ('OBSTETRICIA', 'Obstetricia'),
        ('LECTURA_RESULTADOS', 'Lectura de Resultados'),
    ]

    nombre = models.CharField(max_length=20, choices=ESPECIALIDADES, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.get_nombre_display()

class Doctor(models.Model):
    """
    Médicos del policlínico
    """
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    dni = models.CharField(max_length=8, unique=True, verbose_name='DNI')
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        verbose_name='Especialidad'
    )
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Correo electrónico')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctores'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"Dr. {self.nombres} {self.apellidos} - {self.especialidad.get_nombre_display()}"

    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def especialidad_nombre(self):
        return self.especialidad.get_nombre_display()


    #####
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario del sistema'
    )

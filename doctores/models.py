from django.db import models
from django.contrib.auth.models import User

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
    Médicos del policlínico - AHORA CON MÚLTIPLES ESPECIALIDADES
    """
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    dni = models.CharField(max_length=8, unique=True, verbose_name='DNI')
    
    # ✅ CAMBIO CLAVE: De ForeignKey a ManyToManyField
    especialidades = models.ManyToManyField(
        Especialidad,
        related_name='doctores',
        verbose_name='Especialidades'
    )
    
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Correo electrónico')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario del sistema'
    )

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctores'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        especialidades_str = ", ".join([e.get_nombre_display() for e in self.especialidades.all()])
        return f"Dr. {self.nombres} {self.apellidos} - {especialidades_str}"

    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def especialidades_lista(self):
        """Retorna lista de especialidades como string"""
        return ", ".join([e.get_nombre_display() for e in self.especialidades.all()])
    
    @property
    def especialidad_principal(self):
        """Retorna la primera especialidad (para compatibilidad)"""
        primera = self.especialidades.first()
        return primera.get_nombre_display() if primera else "Sin especialidad"

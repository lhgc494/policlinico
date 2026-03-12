from django.db import models
from django.core.exceptions import ValidationError


class TarifaConsulta(models.Model):

    class TipoConsulta(models.TextChoices):
        GENERAL = 'GENERAL', 'Consulta General'
        ECOGRAFIA = 'ECOGRAFIA', 'Ecografía'
        ESPECIALIDAD = 'ESPECIALIDAD', 'Consulta por Especialidad'
        LECTURA_RESULTADOS = 'LECTURA_RESULTADOS', 'Lectura de Resultados'
        TOPICO = 'TOPICO', 'Tópico / Procedimiento'  # 👈 NUEVA LÍNEA

    class Especialidad(models.TextChoices):
        PEDIATRIA = 'PEDIATRIA', 'Pediatría'
        PSICOLOGIA = 'PSICOLOGIA', 'Psicología'
        OBSTETRICIA = 'OBSTETRICIA', 'Obstetricia'

    tipo_consulta = models.CharField(
        max_length=20,
        choices=TipoConsulta.choices
    )

    especialidad = models.CharField(
        max_length=20,
        choices=Especialidad.choices,
        null=True,
        blank=True
    )

    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # General, Ecografía y Tópico NO deben tener especialidad
        if self.tipo_consulta in [
            self.TipoConsulta.GENERAL,
            self.TipoConsulta.ECOGRAFIA,
            self.TipoConsulta.TOPICO,  # 👈 AGREGADO
        ] and self.especialidad:
            raise ValidationError(
                'Este tipo de consulta no debe tener especialidad.'
            )

        # Especialidad DEBE tener especialidad
        if self.tipo_consulta == self.TipoConsulta.ESPECIALIDAD and not self.especialidad:
            raise ValidationError(
                'Debe seleccionar una especialidad para este tipo de consulta.'
            )

    def save(self, *args, **kwargs):
        # Ejecuta validaciones
        self.full_clean()

        # Si esta tarifa se va a activar, desactiva las anteriores
        if self.activo:
            TarifaConsulta.objects.filter(
                tipo_consulta=self.tipo_consulta,
                especialidad=self.especialidad,
                activo=True
            ).exclude(id=self.id).update(activo=False)

        super().save(*args, **kwargs)

    def __str__(self):
        if self.tipo_consulta == self.TipoConsulta.ESPECIALIDAD:
            return f"{self.get_tipo_consulta_display()} - {self.get_especialidad_display()} - S/ {self.precio}"
        return f"{self.get_tipo_consulta_display()} - S/ {self.precio}"

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone


class HistorialMedico(models.Model):

    consulta = models.OneToOneField(
        'consultas.Consulta',
        on_delete=models.PROTECT,
        related_name='historial'
    )

    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.PROTECT,
        related_name='historiales'
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='historiales_medicos',
        null=True,
        blank=True
    )

    fecha_atencion = models.DateTimeField(default=timezone.now)

    motivo_consulta = models.TextField(null=True, blank=True)

    diagnostico = models.TextField(null=True, blank=True)

    tratamiento = models.TextField(null=True, blank=True)

    indicaciones = models.TextField(blank=True, null=True)

    observaciones = models.TextField(blank=True, null=True)


    def clean(self):
        if self.consulta and self.consulta.estado != "TRIAJE_REALIZADO":
            raise ValidationError(
                "La consulta no está lista para atención médica"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Historial - {self.paciente} - {self.fecha_atencion.date()}"


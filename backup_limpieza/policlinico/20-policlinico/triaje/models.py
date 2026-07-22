from django.db import models
from django.core.exceptions import ValidationError
from consultas.models import Consulta
import re


# ==========================
# VALIDADORES
# ==========================
def validar_presion(value):
    """
    Valida presión arterial en formato 120/80
    """
    if not re.match(r'^\d{2,3}/\d{2,3}$', value):
        raise ValidationError(
            'Formato inválido. Use el formato 120/80'
        )


# ==========================
# MODELO TRIAGE
# ==========================
class Triaje(models.Model):

    # ==========================
    # ESTADOS DEL TRIAGE
    # ==========================
    class EstadoTriaje(models.TextChoices):
        INICIADO = 'INICIADO', 'Iniciado'
        COMPLETO = 'COMPLETO', 'Completo'

    # ==========================
    # RELACIÓN
    # ==========================
    consulta = models.OneToOneField(
        Consulta,
        on_delete=models.PROTECT,
        related_name='triaje'
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoTriaje.choices,
        default=EstadoTriaje.INICIADO
    )

    # ==========================
    # DATOS CLÍNICOS
    # ==========================
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Peso en kilogramos (kg)'
    )

    talla = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Talla en centímetros (cm)'
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Temperatura corporal en °C'
    )

    presion = models.CharField(
        max_length=10,
        blank=True,
        help_text='Presión arterial (ej: 120/80)',
        validators=[validar_presion]
    )

    frecuencia_cardiaca = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Latidos por minuto (lpm)'
    )

    saturacion = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Saturación de oxígeno (%)'
    )

    fecha = models.DateTimeField(auto_now_add=True)

    # ==========================
    # VALIDACIONES DE NEGOCIO
    # ==========================
    def clean(self):
        # Saturación fisiológica
        if self.saturacion is not None and not (50 <= self.saturacion <= 100):
            raise ValidationError({
                'saturacion': 'La saturación debe estar entre 50 y 100 %.'
            })

        # Campos vacíos → triaje inicial
        campos_vacios = all([
            self.peso is None,
            self.talla is None,
            self.temperatura is None,
            not self.presion,
            self.frecuencia_cardiaca is None,
            self.saturacion is None,
        ])

        # Si se intenta guardar datos clínicos
        if not campos_vacios:
            if self.consulta.estado not in [
                Consulta.EstadoConsulta.PAGADA,
                Consulta.EstadoConsulta.EN_TRIAGE
            ]:
                raise ValidationError(
                    'No se puede registrar triaje si la consulta no está pagada.'
                )

    # ==========================
    # GUARDADO Y FLUJO CLÍNICO
    # ==========================
    def save(self, *args, **kwargs):
        self.full_clean()
        creando = self.pk is None
        super().save(*args, **kwargs)

        # Al crear triaje → consulta pasa a EN_TRIAGE
        if creando and self.consulta.estado != Consulta.EstadoConsulta.EN_TRIAGE:
            self.consulta.estado = Consulta.EstadoConsulta.EN_TRIAGE
            self.consulta.save(update_fields=['estado'])

        # Determinar si el triaje está completo
        triaje_completo = all([
            self.peso is not None,
            self.talla is not None,
            self.temperatura is not None,
            self.presion,
            self.frecuencia_cardiaca is not None,
            self.saturacion is not None,
        ])

        if triaje_completo:
            if self.estado != self.EstadoTriaje.COMPLETO:
                self.estado = self.EstadoTriaje.COMPLETO
                super().save(update_fields=['estado'])

            if self.consulta.estado != Consulta.EstadoConsulta.TRIAJE_COMPLETO:
                self.consulta.estado = Consulta.EstadoConsulta.TRIAJE_COMPLETO
                self.consulta.save(update_fields=['estado'])

    def __str__(self):
        return f"Triaje - Consulta #{self.consulta.id}"

    # ==========================
    # PERMISOS PERSONALIZADOS
    # ==========================
    class Meta:
        permissions = [
            ("corregir_triaje", "Puede corregir triajes completados"),
            ("ver_historial_triaje", "Puede ver historial de triajes"),
            ("registrar_triaje", "Puede registrar triaje"),
        ]

from django.db import models
from consultas.models import Consulta


class OrdenPago(models.Model):

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADO = 'PAGADO', 'Pagado'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        YAPE = 'YAPE', 'Yape'
        PLIN = 'PLIN', 'Plin'

    consulta = models.OneToOneField(
        Consulta,
        on_delete=models.PROTECT,
        related_name='orden_pago'
    )

    monto = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        default=EstadoPago.PENDIENTE
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        null=True,
        blank=True
    )

    fecha_pago = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Copiar monto desde la consulta SOLO al crear
        if not self.pk:
            self.monto = self.consulta.precio

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Orden Pago #{self.id} - Consulta {self.consulta.id} - {self.estado}"


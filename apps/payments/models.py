from django.db import models
from django.conf import settings
from apps.classes.models import Reserva


class Pago(models.Model):

    class MetodoPago(models.TextChoices):
        EFECTIVO      = "efectivo",      "Efectivo"
        TARJETA       = "tarjeta",       "Tarjeta"
        TRANSFERENCIA = "transferencia", "Transferencia"

    reserva        = models.OneToOneField(
        Reserva,
        on_delete=models.PROTECT,
        related_name="pago",
        verbose_name="Reserva",
    )
    metodo_pago    = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        verbose_name="Método de pago",
    )
    fecha_pago     = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora del pago",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pagos_registrados",
        verbose_name="Secretario",
    )

    class Meta:
        verbose_name        = "Pago"
        verbose_name_plural = "Pagos"
        ordering            = ["-fecha_pago"]

    def __str__(self):
        return f"Pago #{self.pk} — {self.reserva} [{self.metodo_pago}]"
from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from apps.classes.models import Reserva


class Pago(models.Model):

    class MetodoPago(models.TextChoices):
        EFECTIVO      = "efectivo",      "Efectivo"
        MERCADO_PAGO       = "mercado_pago",       "Mercado Pago    "

    # Estados específicos para pagos online con MercadoPago
    class Estado(models.TextChoices):
        PENDIENTE  = "pendiente",  "Pendiente"
        APROBADO   = "aprobado",   "Aprobado"
        RECHAZADO  = "rechazado",  "Rechazado"
        EN_PROCESO = "en_proceso", "En proceso"
        CANCELADO  = "cancelado",  "Cancelado"

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

    # --- Campos para MercadoPago ---
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name="Estado del pago",
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto",
    )
    preference_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Preference ID (MP)",
    )
    payment_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Payment ID (MP)",
    )

    class Meta:
        verbose_name        = "Pago"
        verbose_name_plural = "Pagos"
        ordering            = ["-fecha_pago"]

    def __str__(self):
        return f"Pago #{self.pk} — {self.reserva} [{self.metodo_pago}]"


@receiver(post_delete, sender=Pago)
def revertir_reserva_al_eliminar_pago(sender, instance, **kwargs):
    """
    Si se elimina un Pago (por ejemplo, desde el admin), la reserva que
    respaldaba ese pago vuelve a quedar como "Reservado" y sin recepcionar
    -- ya no tiene sentido que siga marcada como paga si el pago dejó de
    existir. Solo se toca la reserva si todavía estaba en estado "Pago"
    (si ya la habían cancelado por otro lado, se deja como está).
    """
    Reserva.objects.filter(
        pk=instance.reserva_id,
        estado=Reserva.Estado.PAGO,
    ).update(
        estado=Reserva.Estado.RESERVADO,
        recepcionado=False,
    )
    
    # Propiedades de conveniencia para facilitar la lógica en vistas y templates
    @property
    def es_mercado_pago(self):
        return self.metodo_pago == self.MetodoPago.MERCADO_PAGO
    @property
    def esta_aprobado(self):
        return self.estado == self.Estado.APROBADO

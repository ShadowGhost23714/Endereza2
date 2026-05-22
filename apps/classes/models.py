from time import timezone

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Turno(models.Model):
    """Represents a rehabilitation session slot."""

    class Actividad(models.TextChoices):
        TREN_INFERIOR = "Tren inferior", "Tren inferior"
        ZONA_MEDIA    = "Zona media",    "Zona media"
        TREN_SUPERIOR = "Tren superior", "Tren superior"

    fecha       = models.DateField(verbose_name="Fecha")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    cupo        = models.PositiveIntegerField(verbose_name="Cupo máximo")
    actividad   = models.CharField(
        max_length=20,
        choices=Actividad.choices,
        verbose_name="Actividad",
    )

    class Meta:
        verbose_name        = "Turno"
        verbose_name_plural = "Turnos"
        ordering            = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.actividad} — {self.fecha} {self.hora_inicio.strftime('%H:%M')}"

    def cupos_disponibles(self):
        """Returns the number of available slots (total cupo minus active reservations)."""
        ocupados = self.reservas.filter(estado=Reserva.Estado.RESERVADO).count()
        return max(self.cupo - ocupados, 0)

    def tiene_cupo(self):
        return self.cupos_disponibles() > 0
    @property
    def es_hoy(self):
        """True si el turno es hoy."""
        return self.fecha == timezone.localdate()
    # Si todavía no tenés hora_fin en el modelo, podés derivarla así
    # (asumiendo que las clases duran 1 hora; ajustá a lo que necesites):
    @property
    def hora_fin(self):
        from datetime import datetime, timedelta
        dt = datetime.combine(self.fecha, self.hora_inicio) + timedelta(hours=1)
        return dt.time()


class TurnoProfesional(models.Model):
    """Associates a professional (User) with a Turno."""

    id_turno    = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        related_name="turno_profesionales",
        verbose_name="Turno",
    )
    id_profesor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="turno_profesionales",
        verbose_name="Profesional",
    )

    class Meta:
        verbose_name        = "Turno - Profesional"
        verbose_name_plural = "Turnos - Profesionales"
        unique_together     = ("id_turno", "id_profesor")

    def __str__(self):
        return f"{self.id_profesor} → {self.id_turno}"


class Reserva(models.Model):
    class Estado(models.TextChoices):
        RESERVADO  = "reservado",  "Reservado"
        CANCELADO  = "cancelado",  "Cancelado"
        PAGO       = "pago",       "Pago"

    id_usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservas",
        verbose_name="Paciente",
    )
    id_turno = models.ForeignKey(
        Turno,
        on_delete=models.CASCADE,
        related_name="reservas",
        verbose_name="Turno",
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.RESERVADO,
        verbose_name="Estado",
    )
    recepcionado = models.BooleanField(
        default=False,
        verbose_name="Recepcionado",
    )

    class Meta:
        verbose_name        = "Reserva"
        verbose_name_plural = "Reservas"
        unique_together     = ("id_usuario", "id_turno")

    def __str__(self):
        return f"Reserva #{self.pk} — {self.id_usuario} | {self.id_turno} [{self.estado}]"
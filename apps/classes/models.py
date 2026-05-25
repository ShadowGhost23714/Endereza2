# apps/classes/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.professor.models import Profesor

User = get_user_model()


class Turno(models.Model):
    class Actividad(models.TextChoices):
        TREN_INFERIOR = "tren_inferior", "Tren inferior"
        ZONA_MEDIA    = "zona_media",    "Zona media"
        TREN_SUPERIOR = "tren_superior", "Tren superior"

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
        ocupados = self.reservas.filter(estado=Reserva.Estado.RESERVADO).count()
        return max(self.cupo - ocupados, 0)

    def tiene_cupo(self):
        return self.cupos_disponibles() > 0

    @property
    def es_hoy(self):
        return self.fecha == timezone.localdate()

    @property
    def hora_fin(self):
        from datetime import datetime, timedelta
        dt = datetime.combine(self.fecha, self.hora_inicio) + timedelta(hours=1)
        return dt.time()


class TurnoProfesional(models.Model):
    id_turno    = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="turno_profesionales")
    id_profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name="turno_profesionales")

    class Meta:
        unique_together = ("id_turno", "id_profesor")

    def __str__(self):
        return f"{self.id_profesor} → {self.id_turno}"


class Reserva(models.Model):
    class Estado(models.TextChoices):
        RESERVADO      = "reservado",      "Reservado"
        CANCELADO      = "cancelado",      "Cancelado"
        PAGO           = "pago",           "Pago"
        LISTA_ESPERA   = "lista_espera",   "Lista de espera"   # ← NUEVO

    id_usuario    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservas")
    id_turno      = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="reservas")
    estado        = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.RESERVADO,
    )
    fecha_reserva = models.DateTimeField(auto_now_add=True)   # ← NUEVO

    class Meta:
        unique_together = ("id_usuario", "id_turno")

    @property
    def es_lista_espera(self):
        return self.estado == self.Estado.LISTA_ESPERA

    @property
    def es_pago_confirmado(self):
        return self.estado == self.Estado.PAGO
    
    def notify_cancelling_reserva(self):
        print(f"Notificando a {self.id_usuario} sobre la cancelación de su reserva para el turno {self.id_turno}.")
        # Aquí podrías implementar la lógica real de notificación, como enviar un email o una
        # notificación push, en lugar de solo imprimir un mensaje.
    
    def lista_espera(self):
        return self.estado == self.Estado.LISTA_ESPERA
    
    def pago_hecho(self, pk):
        reserva = Reserva.objects.filter(pk=pk).first()

        devolver = reserva.estado == Reserva.Estado.PAGO
        print(f"Verificando si la reserva #{reserva.pk} tiene el pago hecho: {devolver}.")
        print(f"Estado actual de la reserva: {reserva.estado}.")
        return devolver

    def __str__(self):
        return f"Reserva #{self.pk} — {self.id_usuario} | {self.id_turno} [{self.estado}]"

class Sala(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True)
    capacidad = models.PositiveIntegerField()
    
    class Meta:
        verbose_name        = "Sala"
        verbose_name_plural = "Salas"
        ordering            = ["numero"]
    
    def get_capacidad(id: int) -> int:
        try:
            sala = Sala.objects.get(id=id)
            return sala.capacidad
        except Sala.DoesNotExist:
            return 0  # O podrías lanzar una excepción personalizada aquí
        
    def get_cantidad(self):
        return self.capacidad

    def __str__(self):
        return f"Sala {self.numero} (Capacidad: {self.capacidad})"
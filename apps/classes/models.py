# apps/classes/models.py

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
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
    sala       = models.ForeignKey("Sala", on_delete=models.CASCADE, related_name="turnos")
    actividad   = models.CharField(
        max_length=20,
        choices=Actividad.choices,
        verbose_name="Actividad",
    )
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio"
    )


    class Meta:
        verbose_name        = "Turno"
        verbose_name_plural = "Turnos"
        ordering            = ["fecha", "hora_inicio"]

    def devolver_profesor(self):
        turno_profesional = self.turno_profesionales.select_related("id_profesor").first()
        return turno_profesional.id_profesor if turno_profesional else "profesor random"
    
    def devolver_especialidad(self):
        if self.actividad == self.Actividad.TREN_INFERIOR:
            return "Tren inferior"
        elif self.actividad == self.Actividad.ZONA_MEDIA:
            return "Zona media"
        elif self.actividad == self.Actividad.TREN_SUPERIOR:
            return "Tren superior"
        return "Especialidad desconocida"
    def __str__(self):
        return f"{self.actividad} — {self.fecha} {self.hora_inicio.strftime('%H:%M')}"

    def cupos_disponibles(self):
        ocupados = self.reservas.filter(estado=Reserva.Estado.RESERVADO).count()
        return max(self.cupo - ocupados, 0)

    def tiene_cupo(self):
        return self.cupos_disponibles() > 0
    def profesor_ocupado_en_turno(profesor, fecha, hora_inicio):
        return TurnoProfesional.objects.filter(
            id_profesor=profesor,
            id_turno__fecha=fecha,
            id_turno__hora_inicio=hora_inicio
        ).count() > 0

    @property #devuelve un decimal con el costo de la clase, que se usará para calcular el reembolso
    def get_costo_clase(self):
        return self.precio
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
        LISTA_ESPERA   = "lista_espera",   "Lista de espera"

    id_usuario    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservas")
    id_turno      = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="reservas")
    estado        = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.RESERVADO,
    )
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    recepcionado  = models.BooleanField(
        default=False,
        verbose_name="Recepcionado",
    )

   

    @property
    def es_lista_espera(self):
        return self.estado == self.Estado.LISTA_ESPERA

    @property
    def es_pago_confirmado(self):
        return self.estado == self.Estado.PAGO
    
    def notify_cancelling_reserva(self):
        print(f"Notificando a {self.id_usuario} sobre la cancelación de su reserva para el turno {self.id_turno}.")

    def lista_espera(self):
        return self.estado == self.Estado.LISTA_ESPERA
    
    def pago_hecho(self, pk):
        reserva = Reserva.objects.filter(pk=pk).first()

        devolver = reserva.estado == Reserva.Estado.PAGO
        print(f"Verificando si la reserva #{reserva.pk} tiene el pago hecho: {devolver}.")
        print(f"Estado actual de la reserva: {reserva.estado}.")
        return devolver
    

    @property
    def faltan_mas_de_48_horas(self):
        fecha_turno = timezone.make_aware(
            datetime.combine(
                self.id_turno.fecha,
                self.id_turno.hora_inicio
            )
        )

        diferencia = fecha_turno - timezone.datetime.now().astimezone()  # Asegura que ambas fechas estén en la misma zona horaria

        return diferencia.total_seconds() >= 48 * 60 * 60

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
    
class CertificadoMedico(models.Model):

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        VALIDADO  = "validado",  "Validado"
        RECHAZADO = "rechazado", "Rechazado"

    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.CASCADE,
        related_name="certificado_medico",
        verbose_name="Reserva cancelada",
    )
    imagen = models.ImageField(
        upload_to="certificados_medicos/%Y/%m/",
        verbose_name="Imagen O PDF del certificado",
    )
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name="Estado",
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de envío",
    )
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_revisados",
        verbose_name="Revisado por",
    )
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de revisión",
    )

    class Meta:
        verbose_name        = "Certificado médico"
        verbose_name_plural = "Certificados médicos"
        ordering            = ["-fecha_envio"]

    @property
    def es_pendiente(self):
        return self.estado == self.Estado.PENDIENTE

    def __str__(self):
        return (
            f"Certificado de {self.reserva.id_usuario.nombre_completo} "
            f"— {self.reserva.id_turno} [{self.estado}]"
        )
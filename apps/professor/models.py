# profesores/models.py

from django.db import models


class Profesor(models.Model):

    class Especialidad(models.TextChoices):
        TREN_INFERIOR = "tren_inferior", "Tren inferior"
        ZONA_MEDIA    = "zona_media",    "Zona media"
        TREN_SUPERIOR = "tren_superior", "Tren superior"

    nombre      = models.CharField("Nombre", max_length=100)
    apellido    = models.CharField("Apellido", max_length=100)
    dni         = models.CharField("DNI", max_length=20, unique=True)
    especialidad = models.CharField(
        "Especialidad",
        max_length=20,
        choices=Especialidad.choices,
    )
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Profesor"
        verbose_name_plural = "Profesores"
        ordering            = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} — {self.get_especialidad_display()}"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
from datetime import date
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from datetime import date

class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario.
    """

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("El email es obligatorio.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("tipo", "dueno")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "El superusuario debe tener is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "El superusuario debe tener is_superuser=True."
            )

        return self.create_user(
            email,
            password,
            **extra_fields
        )


class Usuario(AbstractUser):

    # ---------------------------------------------------------
    # TIPOS DE USUARIO
    # ---------------------------------------------------------

    class TipoUsuario(models.TextChoices):
        CLIENTE    = "cliente",    "Cliente"
        SECRETARIO = "secretario", "Secretario"
        DUENO      = "dueno",      "Dueño"

    # ---------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico",
    )

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    # ---------------------------------------------------------
    # DATOS PERSONALES
    # ---------------------------------------------------------

    first_name = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name="Apellido",
    )

    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="DNI",
    )

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento",
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.CLIENTE,
        verbose_name="Tipo de usuario",
    )

    tiene_abono_mensual = models.BooleanField(
        default=False,
        verbose_name="Tiene abono mensual",
    )

    abono_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vencimiento del abono",
    )

    clases_a_favor = models.PositiveIntegerField(
    default=0,
    verbose_name="Clases a favor",
    )

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    class Meta:
        verbose_name        = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering            = ["last_name", "first_name"]

    # ---------------------------------------------------------
    # VALIDACIONES
    # ---------------------------------------------------------

    def clean(self):

        if self.tipo == self.TipoUsuario.CLIENTE:
            pass

        elif self.tipo == self.TipoUsuario.SECRETARIO:
            self.fecha_nacimiento    = None
            self.tiene_abono_mensual = False
            self.abono_vencimiento   = None
            self.clases_a_favor      = 0

        elif self.tipo == self.TipoUsuario.DUENO:
            self.dni                 = None
            self.fecha_nacimiento    = None
            self.tiene_abono_mensual = False
            self.abono_vencimiento   = None
            self.clases_a_favor      = 0

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    @property
    def nombre_completo(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def iniciales(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    @property
    def es_cliente(self):
        return self.tipo == self.TipoUsuario.CLIENTE

    @property
    def es_secretario(self):
        return self.tipo == self.TipoUsuario.SECRETARIO

    @property
    def es_dueno(self):
        return self.tipo == self.TipoUsuario.DUENO

    @property
    def abono_activo(self):
        if not self.tiene_abono_mensual:
            return False
        if self.abono_vencimiento is None:
            return False
        return self.abono_vencimiento >= date.today()

    # ---------------------------------------------------------
    # REPRESENTACIÓN
    # ---------------------------------------------------------

    def __str__(self):
        return f"{self.nombre_completo} ({self.email})"
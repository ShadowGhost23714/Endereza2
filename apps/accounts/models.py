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
        CLIENTE = "cliente", "Cliente"
        SECRETARIO = "secretario", "Secretario"
        DUENO = "dueno", "Dueño"

    # ---------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------

    # Eliminamos username y usamos email para login
    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico",
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]

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

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["last_name", "first_name"]

    # ---------------------------------------------------------
    # VALIDACIONES
    # ---------------------------------------------------------

    def clean(self):

        # -----------------------------------------------------
        # CLIENTE
        # -----------------------------------------------------

        if self.tipo == self.TipoUsuario.CLIENTE:

            if not self.dni:
                raise ValidationError({
                    "dni": "El cliente debe tener DNI."
                })

            if not self.fecha_nacimiento:
                raise ValidationError({
                    "fecha_nacimiento":
                        "El cliente debe tener fecha de nacimiento."
                })

            # Validación de edad mínima (13 años)
            hoy = date.today()

            edad = (
                hoy.year
                - self.fecha_nacimiento.year
                - (
                    (hoy.month, hoy.day)
                    < (
                        self.fecha_nacimiento.month,
                        self.fecha_nacimiento.day
                    )
                )
            )

            if edad < 13:
                raise ValidationError({
                    "fecha_nacimiento":
                        "El usuario debe ser mayor de 13 años."
                })

        # -----------------------------------------------------
        # SECRETARIO
        # -----------------------------------------------------

        elif self.tipo == self.TipoUsuario.SECRETARIO:

            # No guardamos fecha de nacimiento
            self.fecha_nacimiento = None

        # -----------------------------------------------------
        # DUENO
        # -----------------------------------------------------

        elif self.tipo == self.TipoUsuario.DUENO:

            # No guardamos DNI ni fecha de nacimiento
            self.dni = None
            self.fecha_nacimiento = None

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    def save(self, *args, **kwargs):

        # Ejecuta validaciones automáticamente
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
        return (
            f"{self.first_name[:1]}{self.last_name[:1]}"
        ).upper()

    @property
    def es_cliente(self):
        return self.tipo == self.TipoUsuario.CLIENTE

    @property
    def es_secretario(self):
        return self.tipo == self.TipoUsuario.SECRETARIO

    @property
    def es_dueno(self):
        return self.tipo == self.TipoUsuario.DUENO

    # ---------------------------------------------------------
    # REPRESENTACIÓN
    # ---------------------------------------------------------

    def __str__(self):
        return f"{self.nombre_completo} ({self.email})"
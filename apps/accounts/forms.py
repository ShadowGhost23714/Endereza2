from datetime import date
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from .models import Usuario

# ==========================================================
# REGISTRO
# ==========================================================

class RegistroForm(UserCreationForm):
    """
    Formulario de registro público.

    Solo permite registrar usuarios tipo CLIENTE.
    """

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "tucorreo@email.com",
                "autocomplete": "email",
            }
        ),
    )

    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu nombre",
                "autocomplete": "given-name",
            }
        ),
    )

    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Tu apellido",
                "autocomplete": "family-name",
            }
        ),
    )

    dni = forms.CharField(
        label="DNI",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Número de DNI",
                "inputmode": "numeric",
            }
        ),
    )

    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "autocomplete": "bday",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):

        model = Usuario

        fields = (
            "email",
            "first_name",
            "last_name",
            "dni",
            "fecha_nacimiento",
            "password1",
            "password2",
        )

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    def clean_fecha_nacimiento(self):

        fecha = self.cleaned_data["fecha_nacimiento"]

        hoy = date.today()

        edad = (
            hoy.year
            - fecha.year
            - (
                (hoy.month, hoy.day)
                < (fecha.month, fecha.day)
            )
        )

        if edad < 13:
            raise forms.ValidationError(
                "Debes ser mayor de 13 años."
            )

        return fecha

    # ------------------------------------------------------
    # SAVE
    # ------------------------------------------------------

    def save(self, commit=True):

        user = super().save(commit=False)

        user.tipo = Usuario.TipoUsuario.CLIENTE

        if commit:
            user.save()

        return user


# ==========================================================
# LOGIN
# ==========================================================

class LoginForm(AuthenticationForm):
    """
    Formulario de login usando email.
    """

    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "tucorreo@email.com",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Tu contraseña",
                "autocomplete": "current-password",
            }
        ),
    )


# ==========================================================
# PERFIL
# ==========================================================

class PerfilForm(forms.ModelForm):
    """
    Formulario para editar perfil de usuario.
    """

    class Meta:

        model = Usuario

        fields = (
            "first_name",
            "last_name",
            "dni",
            "fecha_nacimiento",
            "email",
        )

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Tu nombre",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Tu apellido",
                }
            ),

            "dni": forms.TextInput(
                attrs={
                    "placeholder": "Número de DNI",
                    "inputmode": "numeric",
                }
            ),

            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "tucorreo@email.com",
                }
            ),
        }

    # ------------------------------------------------------
    # INIT
    # ------------------------------------------------------

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        usuario = self.instance

        # --------------------------------------------------
        # DUEÑO
        # --------------------------------------------------

        if usuario.es_dueno:

            self.fields.pop("dni")
            self.fields.pop("fecha_nacimiento")

        # --------------------------------------------------
        # SECRETARIO
        # --------------------------------------------------

        elif usuario.es_secretario:

            self.fields.pop("fecha_nacimiento")
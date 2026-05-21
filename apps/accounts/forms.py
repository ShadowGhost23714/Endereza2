from datetime import date
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

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
        error_messages={
            "invalid": "Correo electrónico inválido."
        }
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
                "min": "1900-01-01",
                "max": date.today().isoformat(),
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

    def clean_dni(self):
        dni = self.cleaned_data["dni"]

        if Usuario.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Ya existe una cuenta con este DNI.")
        
        if not dni.isdigit():
            raise forms.ValidationError("El DNI solo puede contener números.")

        if len(dni) < 7 or len(dni) > 8:
            raise forms.ValidationError("Ingrese un DNI válido.")
        
        return dni
    
    def clean_email(self):
        email = self.cleaned_data["email"]

        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        
        return email

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data["fecha_nacimiento"]

        if fecha.year < 1900 or fecha > date.today():
            raise forms.ValidationError("Fecha inválida.")
        
        hoy = date.today()
        edad = (
            hoy.year
            - fecha.year
            - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        )
        if edad < 13:
            raise forms.ValidationError("Debes ser mayor de 13 años.")
        
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
        error_messages={
        "invalid": "Ingrese un correo electrónico válido."
        }
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

    error_messages = {
        "invalid_login": (
            "El correo o la contraseña son incorrectos."
        ),
    }


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

class CrearSecretarioForm(UserCreationForm):
    """
    Formulario para que el dueño cree una cuenta de tipo Secretario.

    Campos requeridos: nombre, apellido, email, DNI, contraseña x2.
    No solicita fecha de nacimiento (el modelo la descarta para secretarios).
    """

    # ------------------------------------------------------------------
    # CAMPOS
    # ------------------------------------------------------------------

    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(attrs={"placeholder": "Nombre"}),
    )

    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        widget=forms.TextInput(attrs={"placeholder": "Apellido"}),
    )

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "secretario@email.com"}),
    )

    dni = forms.CharField(
        max_length=8,
        label="DNI",
        widget=forms.TextInput(attrs={"placeholder": "12345678"}),
    )

    # ------------------------------------------------------------------
    # META
    # ------------------------------------------------------------------

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email", "dni")

    # ------------------------------------------------------------------
    # VALIDACIONES DE CAMPO
    # ------------------------------------------------------------------

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario registrado con ese correo electrónico.")

        return email

    def clean_dni(self):
        dni = self.cleaned_data.get("dni", "").strip()

        if not dni.isdigit():
            raise ValidationError("El DNI solo puede contener números.")

        if not (7 <= len(dni) <= 8):
            raise ValidationError("El DNI debe tener entre 7 y 8 dígitos.")

        if Usuario.objects.filter(dni=dni).exists():
            raise ValidationError("Ya existe un usuario registrado con ese DNI.")

        return dni

    # ------------------------------------------------------------------
    # GUARDADO
    # ------------------------------------------------------------------
    
    def save(self, commit=True):
        """Fuerza el tipo a SECRETARIO antes de persistir."""
        user = super().save(commit=False)
        user.tipo = Usuario.TipoUsuario.SECRETARIO
        # El modelo ya descarta fecha_nacimiento en clean() para secretarios,
        # pero lo dejamos explícito para mayor claridad.
        user.fecha_nacimiento = None

        if commit:
            user.save()

        return user
    

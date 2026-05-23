# profesores/forms.py

import re

from django import forms

from .models import Profesor


class ProfesorForm(forms.ModelForm):

    class Meta:
        model  = Profesor
        fields = ["nombre", "apellido", "dni", "especialidad"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "placeholder": "Ej: María",
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                         "focus:ring-teal-500 focus:border-teal-500 block w-full p-2.5 "
                         "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
                         "dark:text-white dark:focus:ring-teal-500 dark:focus:border-teal-500",
            }),
            "apellido": forms.TextInput(attrs={
                "placeholder": "Ej: González",
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                         "focus:ring-teal-500 focus:border-teal-500 block w-full p-2.5 "
                         "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
                         "dark:text-white dark:focus:ring-teal-500 dark:focus:border-teal-500",
            }),
            "dni": forms.TextInput(attrs={
                "placeholder": "Ej: 30123456",
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                         "focus:ring-teal-500 focus:border-teal-500 block w-full p-2.5 "
                         "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
                         "dark:text-white dark:focus:ring-teal-500 dark:focus:border-teal-500",
            }),
            "especialidad": forms.Select(attrs={
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                         "focus:ring-teal-500 focus:border-teal-500 block w-full p-2.5 "
                         "dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 "
                         "dark:text-white dark:focus:ring-teal-500 dark:focus:border-teal-500",
            }),
        }
        labels = {
            "nombre":      "Nombre",
            "apellido":    "Apellido",
            "dni":         "DNI",
            "especialidad": "Especialidad",
        }
        error_messages = {
            "dni": {
                "unique": "Ya existe un profesor registrado con ese DNI.",
            },
        }

    # ── Custom validators ──────────────────────────────────────────────────────

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if not re.fullmatch(r"[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+", nombre):
            raise forms.ValidationError(
                "El nombre solo puede contener letras, espacios, guiones y apóstrofes."
            )
        return nombre.title()

    def clean_apellido(self):
        apellido = self.cleaned_data["apellido"].strip()
        if not re.fullmatch(r"[A-Za-záéíóúÁÉÍÓÚüÜñÑ\s\-']+", apellido):
            raise forms.ValidationError(
                "El apellido solo puede contener letras, espacios, guiones y apóstrofes."
            )
        return apellido.title()

    def clean_dni(self):
        dni = self.cleaned_data["dni"].strip().replace(".", "").replace(" ", "")
        if not re.fullmatch(r"\d{7,8}", dni):
            raise forms.ValidationError(
                "El DNI debe contener entre 7 y 8 dígitos numéricos."
            )
        return dni

from datetime import date, datetime, time
from django import forms
from .models import Turno


class TurnoForm(forms.ModelForm):
    """Form for creating and editing a Turno."""

    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
            },
        ),
        label="Fecha",
    )

    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "type": "time",
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "min": "08:00",
                "max": "20:00",
            },
        ),
        label="Hora de inicio",
    )

    cupo = forms.IntegerField(
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "placeholder": "Ej: 10",
            },
        ),
        label="Cupo máximo",
    )

    actividad = forms.ChoiceField(
        choices=Turno.Actividad.choices,
        widget=forms.Select(
            attrs={
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
            },
        ),
        label="Actividad",
    )

    class Meta:
        model  = Turno
        fields = ["fecha", "hora_inicio", "cupo", "actividad"]

    def clean_cupo(self):
        cupo = self.cleaned_data.get("cupo")
        if cupo is not None and cupo < 1:
            raise forms.ValidationError("El cupo debe ser al menos 1.")
        return cupo

    def clean(self):
        cleaned_data = super().clean()
        fecha       = cleaned_data.get("fecha")
        hora_inicio = cleaned_data.get("hora_inicio")
        actividad   = cleaned_data.get("actividad")

        if fecha and hora_inicio and actividad:
            # Prevent duplicate slot: same date + time + activity
            # 1. Validar que la hora sea en punto (Minutos y Segundos == 0)
            if hora_inicio.minute != 0 or hora_inicio.second != 0:
                raise forms.ValidationError(
                    "La hora de inicio debe ser en punto (ej: 08:00, 09:00)."
                )
            # 2. Validar rango estricto de horas (de 08:00 a 20:00)
            if hora_inicio < time(8, 0) or hora_inicio > time(20, 0):
                raise forms.ValidationError(
                    "La hora de inicio debe estar entre las 08:00 y las 20:00 hs."
                )
            qs = Turno.objects.filter(
                fecha=fecha,
                hora_inicio=hora_inicio,
                actividad=actividad,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Ya existe un turno con esa actividad, fecha y hora de inicio."
                )
            if fecha < Turno.objects.earliest("fecha").fecha:
                raise forms.ValidationError("La fecha no puede ser en el pasado.")
            if fecha < Turno.objects.earliest("fecha").fecha or (fecha == Turno.objects.earliest("fecha").fecha and hora_inicio < Turno.objects.earliest("hora_inicio").hora_inicio):
                raise forms.ValidationError("La hora de inicio no puede ser en el pasado.")
            if hora_inicio < Turno.objects.earliest("hora_inicio").hora_inicio or hora_inicio > Turno.objects.latest("hora_inicio").hora_inicio:
                raise forms.ValidationError("La hora de inicio debe estar entre las 08:00 y las 20:00.")

        return cleaned_data
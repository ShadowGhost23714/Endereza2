from django import forms
from apps.classes.models import Reserva, Turno
from .models import Pago


class BuscarTurnoForm(forms.Form):
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha",
    )
    hora = forms.ChoiceField(
        choices=[],
        label="Hora de inicio",
    )
    actividad = forms.ChoiceField(
        choices=[("", "---------")] + Turno.Actividad.choices,
        label="Tipo de clase",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hora"].choices = [
            (f"{h:02d}:00", f"{h:02d}:00")
            for h in range(8, 21)
        ]


class RegistrarPagoForm(forms.Form):
    reserva     = forms.ModelChoiceField(
        queryset=Reserva.objects.none(),
        label="Paciente (DNI)",
        empty_label="Seleccionar paciente...",
    )
    metodo_pago = forms.ChoiceField(
        choices=Pago.MetodoPago.choices,
        label="Método de pago",
    )

    def __init__(self, *args, reservas_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if reservas_qs is not None:
            self.fields["reserva"].queryset = reservas_qs
            # Etiqueta personalizada con rango horario
            self.fields["reserva"].label_from_instance = self._label_reserva

    @staticmethod
    def _label_reserva(reserva):
        from datetime import datetime, timedelta
        turno = reserva.id_turno
        hora_inicio = turno.hora_inicio
        hora_fin = (
            datetime.combine(turno.fecha, hora_inicio) + timedelta(hours=1)
        ).time()
        usuario = reserva.id_usuario
        nombre = usuario.get_full_name() or usuario.username
        return (
            f"{nombre} — {turno.actividad} "
            f"{turno.fecha} "
            f"{hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}"
        )

    def clean_reserva(self):
        reserva = self.cleaned_data["reserva"]
        if reserva.estado != Reserva.Estado.RESERVADO:
            raise forms.ValidationError("Este turno ya fue pagado o cancelado.")
        if hasattr(reserva, "pago"):
            raise forms.ValidationError("Esta reserva ya tiene un pago registrado.")
        return reserva
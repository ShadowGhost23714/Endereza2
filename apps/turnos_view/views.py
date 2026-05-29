from django.shortcuts import render

# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.utils import timezone

from apps.classes.models import Turno, Reserva
from apps.payments.models import Pago


class SecretarioRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_staff or user.es_secretario


class TurnosDelDiaView(LoginRequiredMixin, SecretarioRequiredMixin, TemplateView):
    template_name = "turnos_view/turnos_del_dia.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        ctx["fecha_default"]    = hoy.strftime("%Y-%m-%d")
        ctx["horas"] = [f"{h:02d}:00" for h in range(8, 21)]
        ctx["actividad_default"] = Turno.Actividad.TREN_SUPERIOR
        ctx["actividades"]      = Turno.Actividad.choices
        ctx["metodos_pago"]     = Pago.MetodoPago.choices
        return ctx
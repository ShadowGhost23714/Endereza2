from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from apps.payments.models import Pago

@method_decorator(never_cache, name="dispatch")
class HistorialPagosView(LoginRequiredMixin, TemplateView):
    template_name = "historial_pagos/historial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Solo los pagos de reservas que pertenecen al usuario autenticado
        pagos = (
            Pago.objects.filter(reserva__id_usuario=self.request.user)
            .select_related("reserva", "reserva__id_turno")
            .order_by("-fecha_pago")
        )
        context["pagos"] = pagos
        return context

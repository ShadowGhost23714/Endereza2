from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.db.models import Q
from apps.payments.models import Pago


@method_decorator(never_cache, name="dispatch")
class HistorialPagosView(LoginRequiredMixin, TemplateView):
    template_name = "historial_pagos/historial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pagos = (
            Pago.objects.filter(reserva__id_usuario=self.request.user)
            .filter(
                # Efectivo: siempre se muestra (no pasa por el flujo de estados de MP).
                # Mercado Pago: solo se muestra si el pago quedó aprobado.
                Q(metodo_pago=Pago.MetodoPago.EFECTIVO)
                | Q(metodo_pago=Pago.MetodoPago.MERCADO_PAGO, estado=Pago.Estado.APROBADO)
            )
            .select_related("reserva", "reserva__id_turno", "reserva__certificado_medico")
            .order_by("-fecha_pago")
        )
        context["pagos"] = pagos
        return context
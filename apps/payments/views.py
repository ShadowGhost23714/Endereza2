from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.db import transaction
from datetime import time as time_type

from apps.classes.models import Reserva, Turno
from .forms import BuscarTurnoForm, RegistrarPagoForm
from .models import Pago


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class RegistrarPagoView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "payments/registrar_pago.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["buscar_form"] = BuscarTurnoForm()
        ctx["pago_form"]   = None
        ctx["reservas"]    = None
        return ctx

    def post(self, request, *args, **kwargs):
        # ── Paso 1: buscar turnos ──────────────────────────────────────────
        if "mostrar_turnos" in request.POST:
            buscar_form = BuscarTurnoForm(request.POST)

            if buscar_form.is_valid():
                fecha     = buscar_form.cleaned_data["fecha"]
                hora_str = buscar_form.cleaned_data["hora"] 
                hora = time_type(int(hora_str[:2]), 0)
                actividad = buscar_form.cleaned_data["actividad"]

                # Buscar el turno que coincida
                turno = Turno.objects.filter(
                    fecha=fecha,
                    hora_inicio=hora,
                    actividad=actividad,
                ).first()

                if turno is None:
                    messages.warning(request, "No se encontraron turnos reservados.")
                    return self.render_to_response(
                        {"buscar_form": buscar_form, "pago_form": None, "reservas": None}
                    )

                # Reservas pendientes de pago para ese turno
                reservas_qs = Reserva.objects.filter(
                    id_turno=turno,
                    estado=Reserva.Estado.RESERVADO,
                ).select_related("id_usuario")

                if not reservas_qs.exists():
                    messages.warning(request, "No se encontraron turnos reservados.")
                    return self.render_to_response(
                        {"buscar_form": buscar_form, "pago_form": None, "reservas": None}
                    )

                pago_form = RegistrarPagoForm(reservas_qs=reservas_qs)
                return self.render_to_response({
                    "buscar_form": buscar_form,
                    "pago_form":   pago_form,
                    "turno":       turno,
                    # Guardamos los datos del turno para el paso 2
                    "turno_id":    turno.pk,
                })

            # Formulario de búsqueda inválido
            return self.render_to_response(
                {"buscar_form": buscar_form, "pago_form": None, "reservas": None}
            )

        # ── Paso 2: registrar pago ─────────────────────────────────────────
        if "registrar_pago" in request.POST:
            turno_id = request.POST.get("turno_id")
            turno    = Turno.objects.filter(pk=turno_id).first()

            reservas_qs = Reserva.objects.filter(
                id_turno=turno,
                estado=Reserva.Estado.RESERVADO,
            ).select_related("id_usuario") if turno else Reserva.objects.none()

            pago_form   = RegistrarPagoForm(request.POST, reservas_qs=reservas_qs)
            buscar_form = BuscarTurnoForm()

            if pago_form.is_valid():
                reserva     = pago_form.cleaned_data["reserva"]
                metodo_pago = pago_form.cleaned_data["metodo_pago"]

                with transaction.atomic():
                    # 1. Crear el registro de pago
                    Pago.objects.create(
                        reserva=reserva,
                        metodo_pago=metodo_pago,
                        registrado_por=request.user,
                    )
                    # 2. Actualizar estado de la reserva
                    reserva.estado = Reserva.Estado.PAGO
                    reserva.save(update_fields=["estado"])

                messages.success(
                    request,
                    f"Pago registrado correctamente para "
                    f"{reserva.id_usuario.get_full_name() or reserva.id_usuario.username}."
                )
                return redirect("payments:registrar_pago")

            return self.render_to_response({
                "buscar_form": buscar_form,
                "pago_form":   pago_form,
                "turno":       turno,
                "turno_id":    turno_id,
            })
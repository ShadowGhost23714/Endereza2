# apps/classes/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import ListView, View
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TurnoForm
from .models import Reserva, Turno
from .emails import enviar_confirmacion_reserva, enviar_confirmacion_lista_espera


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
    
class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class TurnoCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model         = Turno
    form_class    = TurnoForm
    template_name = "classes/turno_create.html"
    success_url   = reverse_lazy("turnos:listar_clases")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"El turno fue creado exitosamente: {self.object}")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Por favor corregí los errores indicados antes de continuar.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Nuevo turno"
        return ctx



class TurnoListView(ListView):
    model                = Turno
    template_name        = "classes/listar_clases.html"
    context_object_name  = "turnos"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            # Mostrar solo turnos futuros para usuarios autenticados
            return Turno.objects.filter(
                fecha__gte=timezone.now().date()
            ).order_by("fecha", "hora_inicio")
        return Turno.objects.all().order_by("fecha", "hora_inicio")
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Dict: {turno_id: estado_reserva} para el usuario actual
            reservas_usuario = Reserva.objects.filter(
                id_usuario=self.request.user
            ).values_list("id_turno_id", "estado")
            ctx["mis_reservas"] = dict(reservas_usuario)
        else:
            ctx["mis_reservas"] = {}
        return ctx


class TurnoDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    model         = Turno
    template_name = "classes/turno_delete.html"
    success_url   = reverse_lazy("turnos:turno_delete", kwargs={"pk": 0})  # Placeholder, se redirige manualmente

    def post(self, request, pk):
        try:
            turno = get_object_or_404(Turno, pk=pk)
            
            reservas = Reserva.objects.filter(id_turno = turno.pk)
            for reserva in reservas:
                reserva.notify_cancelling_reserva()  # Notificar a los usuarios afectados por la cancelación
                reserva.delete()  # Eliminar las reservas asociadas al turno
            turno.delete() #elimino el turno
            messages.success(request, "Turno eliminado exitosamente.")
            return redirect("turnos:listar_clases")
        except Exception as e:
            messages.error(request, "Error al eliminar el turno.")
            return redirect("turnos:listar_clases")

class ReservaListView(LoginRequiredMixin, ListView):
    model               = Reserva
    template_name       = "classes/reserva_list.html"
    context_object_name = "reservas"

    def get_queryset(self):
        return Reserva.objects.filter(id_usuario=self.request.user).order_by("-fecha_reserva")

class ReservasAsociadasView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model               = Reserva
    template_name       = "classes/reservas_asociadas.html"
    context_object_name = "reservas_asociadas"

    def get_queryset(self):
        render(self.request, "classes/reservas_asociadas.html", {"turno_id": self.kwargs.get("turno_id")})
        turno_id = self.kwargs.get("turno_id")
        print(f"Obteniendo reservas asociadas al turno_id={turno_id}")
        return Reserva.objects.filter(id_turno=turno_id).select_related("id_usuario").order_by("-fecha_reserva")


class MisClasesView(LoginRequiredMixin, ListView):
    model               = Reserva
    template_name       = "classes/mis_clases.html"
    context_object_name = "reservas"

    def get_queryset(self):
        return (
            Reserva.objects
            .filter(
                id_usuario=self.request.user,
                estado__in=[Reserva.Estado.RESERVADO, Reserva.Estado.LISTA_ESPERA],
            )
            .select_related("id_turno")
            .order_by("id_turno__fecha", "id_turno__hora_inicio")
        )


@login_required
def reservar_clase(request, turno_id):
    """
    Escenario 1 / 2 : reserva exitosa (con o sin cupo restante).
    Escenario 4     : conflicto de horario.
    """
    if request.method != "POST":
        return redirect("turnos:listar_clases")

    turno = get_object_or_404(Turno, pk=turno_id)

    # ── Escenario 4: ya tiene una reserva activa en el mismo horario ──────────
    conflicto = Reserva.objects.filter(
        id_usuario   = request.user,
        estado       = Reserva.Estado.RESERVADO,
        id_turno__fecha       = turno.fecha,
        id_turno__hora_inicio = turno.hora_inicio,
    ).exclude(id_turno=turno).first()

    if conflicto:
        messages.error(
            request,
            "Ya tenés reservada una clase en este horario. "
            "Si querés reservar esta clase, cancelá tu otra reserva."
        )
        return redirect("turnos:listar_clases")

    # ── Reserva ya existente para este mismo turno ────────────────────────────
    reserva_existente = Reserva.objects.filter(
        id_usuario=request.user,
        id_turno=turno,
    ).first()

    if reserva_existente:
        if reserva_existente.estado == Reserva.Estado.RESERVADO:
            messages.info(request, "Ya tenés una reserva para este turno.")
        elif reserva_existente.estado == Reserva.Estado.LISTA_ESPERA:
            messages.info(request, "Ya estás anotado en la lista de espera de este turno.")
        return redirect("turnos:mis_clases")

    # ── Sin cupo: lista de espera (Escenario 3) ───────────────────────────────
    if not turno.tiene_cupo():
        messages.error(request, "No hay cupos disponibles para este turno.")
        return redirect("turnos:listar_clases")

    # ── Reserva exitosa (Escenarios 1 y 2) ───────────────────────────────────
    reserva = Reserva.objects.create(
        id_usuario = request.user,
        id_turno   = turno,
        estado     = Reserva.Estado.RESERVADO,
    )
    enviar_confirmacion_reserva(reserva)
    messages.success(request, "¡Reserva creada correctamente! Te enviamos un mail de confirmación.")
    return redirect("turnos:mis_clases")


@login_required
def anotarse_lista_espera(request, turno_id):
    """Escenario 3: anotarse en lista de espera cuando no hay cupo."""
    if request.method != "POST":
        return redirect("turnos:listar_clases")

    turno = get_object_or_404(Turno, pk=turno_id)

    if turno.tiene_cupo():
        messages.info(request, "Hay cupos disponibles, podés reservar directamente.")
        return redirect("turnos:listar_clases")

    reserva_existente = Reserva.objects.filter(
        id_usuario=request.user,
        id_turno=turno,
    ).first()

    if reserva_existente:
        messages.info(request, "Ya estás anotado en este turno.")
        return redirect("turnos:mis_clases")

    reserva = Reserva.objects.create(
        id_usuario = request.user,
        id_turno   = turno,
        estado     = Reserva.Estado.LISTA_ESPERA,
    )
    enviar_confirmacion_lista_espera(reserva)
    messages.success(request, "Te anotamos en la lista de espera. Te avisamos si se libera un cupo.")
    return redirect("turnos:mis_clases")
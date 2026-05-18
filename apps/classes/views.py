from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .forms import TurnoForm
from .models import Reserva, Turno


class StaffRequiredMixin(UserPassesTestMixin):
    """Restricts the view to staff / admin users only."""

    def test_func(self):
        return self.request.user.is_staff


class TurnoCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """
    Displays a form to create a new Turno and handles its validation.

    Access: staff users only.
    On success: redirects to the turno list (or detail) page and shows a success message.
    """

    model         = Turno
    form_class    = TurnoForm
    template_name = "classes/turno_create.html"
    success_url   = reverse_lazy("turnos:turno_create")   # adjust to your URL name

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"El turno fue creado exitosamente: {self.object}",
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Por favor corregí los errores indicados antes de continuar.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Nuevo turno"
        return ctx

class TurnoListView(ListView):
    model = Turno
    template_name = "classes/listar_clases.html"
    context_object_name = "turnos"
    success_url = reverse_lazy("turnos:listar_clases")

    def get_queryset(self):
        """Returns all turnos ordered by date and time."""
        return Turno.objects.all().order_by("fecha", "hora_inicio")

class ReservaListView(LoginRequiredMixin, ListView):
    model = Reserva
    template_name = "classes/reserva_list.html"
    context_object_name = "reservas"

    def get_queryset(self): # muestra solo las reservas del usuario logueado, ordenadas por fecha de reserva descendente
        return Reserva.objects.filter(id_usuario=self.request.user).order_by("-fecha_reserva")

@login_required
def reservar_clase(request, turno_id):
    turno = get_object_or_404(Turno, pk=turno_id)
    if turno.cupos_disponibles() <= 0:
        messages.error(request, "No hay cupos disponibles para este turno.")
        return redirect("turnos:listar_clases")

    reserva, created = Reserva.objects.get_or_create(
        id_usuario=request.user,
        id_turno=turno,
        defaults={"estado": Reserva.Estado.RESERVADO},
    )
    if created:
        messages.success(request, "Reserva creada correctamente.")
    else:
        messages.info(request, "Ya tenés una reserva para este turno.")
    return redirect("turnos:mis_clases")
# Agregá esto en apps/classes/views.py
# (importá lo necesario junto a tus imports existentes)

class MisClasesView(LoginRequiredMixin, ListView):
    """
    Muestra las reservas activas (estado='reservado') del usuario autenticado,
    ordenadas por fecha y hora de inicio, solo desde hoy en adelante.
    """
    model = Reserva
    template_name = "classes/mis_clases.html"
    context_object_name = "reservas"
    success_url   = reverse_lazy("turnos:mis_clases")

    def get_queryset(self):
        hoy = timezone.localdate()
        return (
            Reserva.objects.filter(
                id_usuario=self.request.user,
                estado=Reserva.Estado.RESERVADO,          # ajustá si tu TextChoices tiene otro nombre
                id_turno__fecha__gte=hoy,
            )
            .select_related("id_turno")
            .order_by("id_turno__fecha", "id_turno__hora_inicio")
        )


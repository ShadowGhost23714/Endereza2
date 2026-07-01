# apps/classes/views.py
from django.contrib import messages
from django.template.response import TemplateResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import ListView, View
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime, timedelta
from apps.classes.models import CertificadoMedico
from apps.core import models
from apps.accounts import models
from apps.payments.models import Pago
from apps.professor.models import Profesor
from apps.classes.models import CertificadoMedico

from .forms import TurnoForm
from .models import Reserva, Turno, TurnoProfesional
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
        turno = form.save()  # Guarda el Turno
        profesor = form.cleaned_data['profesor']
        TurnoProfesional.objects.create(id_turno=turno, id_profesor=profesor)
        messages.success(self.request, f"El turno fue creado exitosamente: {turno}")
        return redirect(self.success_url)

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
                estado__in=[Reserva.Estado.RESERVADO, Reserva.Estado.LISTA_ESPERA, Reserva.Estado.PAGO],
                id_turno__fecha__gte=timezone.now().date()
            )
            .select_related("id_turno")
            .order_by("id_turno__fecha", "id_turno__hora_inicio")
        )

@login_required
def cancelar_reserva(request, reserva_id):

    if request.method != "POST":
        return redirect("turnos:mis_clases")

    reserva = get_object_or_404(
        Reserva,
        pk=reserva_id,
        id_usuario=request.user
    )

    fecha_turno = datetime.combine(
        reserva.id_turno.fecha,
        reserva.id_turno.hora_inicio
    )

    faltan_mas_48 = (
        fecha_turno - timezone.datetime.now()
    ) >= timedelta(hours=48)

    tipo = request.POST.get("tipo_reembolso")

    if faltan_mas_48:
        if tipo == "saldo":
            request.user.saldo_a_favor += reserva.id_turno.get_costo_clase
            request.user.save(update_fields=["saldo_a_favor"])
            Pago.objects.filter(reserva=reserva).update(reembolsado=True)
            reserva.estado = Reserva.Estado.CANCELADO
        else:
            reserva.estado = Reserva.Estado.DEVOLVER_DINERO
        reserva.save()

        messages.success(
            request,
            "Reserva cancelada correctamente."
        )

        return redirect("turnos:mis_clases")
    
    if tipo == "saldo":
        request.user.save(update_fields=["saldo_a_favor"])
        reserva.estado = Reserva.Estado.CANCELADO
    else:
        reserva.estado = Reserva.Estado.DEVOLVER_DINERO

    archivo = request.FILES.get("certificado")

    if not archivo:
        messages.error(
            request,
            "Debés adjuntar un certificado médico."
        )
        return redirect("turnos:mis_clases")

    CertificadoMedico.objects.create(
        reserva=reserva,
        imagen=archivo,
    )

    if tipo != "saldo":
        reserva.estado = Reserva.Estado.DEVOLVER_DINERO
    else:
        reserva.estado = Reserva.Estado.CANCELADO
    reserva.save()

    messages.success(
        request,
        "Certificado enviado correctamente. Será revisado por administración."
    )

    return redirect("turnos:mis_clases")

@login_required
def reservar_clase(request, turno_id, efectivo):
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
        id_turno__fecha       = turno.fecha,
        id_turno__hora_inicio = turno.hora_inicio,
    ).exclude(id_turno=turno).exclude(estado=Reserva.Estado.CANCELADO).first()

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
    ).exclude(estado=Reserva.Estado.CANCELADO).first()

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

    if efectivo:
        reserva = Reserva.objects.create(
            id_usuario = request.user,
            id_turno   = turno,
            estado     = Reserva.Estado.RESERVADO,
        )
    else:
        # ── Reserva exitosa (Escenarios 1 y 2) ───────────────────────────────────
        reserva = Reserva.objects.create(
            id_usuario = request.user,
            id_turno   = turno,
            estado     = Reserva.Estado.PAGO,
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

@login_required
def reservar_saldo_a_favor(request, turno_id):
    if request.method != "POST":
        return redirect("turnos:listar_clases")

    turno = get_object_or_404(Turno, pk=turno_id)

    # Verificar que tiene saldo a favor
    if request.user.saldo_a_favor < turno.get_costo_clase:
        messages.error(request, "No tenés saldo a favor suficiente.")
        return redirect("turnos:listar_clases")

    # Conflicto de horario
    conflicto = Reserva.objects.filter(
        id_usuario=request.user,
        id_turno__fecha=turno.fecha,
        id_turno__hora_inicio=turno.hora_inicio,
    ).exclude(id_turno=turno).exclude(estado=Reserva.Estado.CANCELADO).first()

    if conflicto:
        messages.error(request, "Ya tenés reservada una clase en este horario.")
        return redirect("turnos:listar_clases")

    # Reserva ya existente
    reserva_existente = Reserva.objects.filter(
        id_usuario=request.user,
        id_turno=turno,
    ).exclude(estado=Reserva.Estado.CANCELADO).first()

    if reserva_existente:
        messages.info(request, "Ya tenés una reserva para este turno.")
        return redirect("turnos:mis_clases")

    # Sin cupo
    if not turno.tiene_cupo():
        messages.error(request, "No hay cupos disponibles para este turno.")
        return redirect("turnos:listar_clases")

    from django.db import transaction
    from apps.payments.models import Pago
    with transaction.atomic():
        reserva = Reserva.objects.create(
            id_usuario = request.user,
            id_turno   = turno,
            estado     = Reserva.Estado.PAGO,
        )
        Pago.objects.create(
            reserva        = reserva,
            metodo_pago    = "saldo_a_favor",
            registrado_por = None,
        )
        request.user.saldo_a_favor -= turno.get_costo_clase
        request.user.save(update_fields=["saldo_a_favor"])

    enviar_confirmacion_reserva(reserva)
    messages.success(request, "¡Reserva creada con saldo a favor! Te enviamos un mail de confirmación.")
    return redirect("turnos:mis_clases")

@login_required
def lista_certificados(request):
    if not (request.user.es_dueno or request.user.es_secretario):
        messages.error(request, "No tenés permisos para acceder a esta sección.")
        return redirect("home")

    certificados = (
        CertificadoMedico.objects
        .filter(estado=CertificadoMedico.Estado.PENDIENTE)
        .select_related("reserva__id_usuario", "reserva__id_turno")
        .order_by("-fecha_envio")
    )
    return TemplateResponse(request, "classes/certificados_list.html", {"certificados": certificados})

@login_required
def lista_devolver_dinero(request):
    if not (request.user.es_dueno or request.user.es_secretario):
        messages.error(request, "No tenés permisos para acceder a esta sección.")
        return redirect("home")

    #lista de reservas que tienen estado "devolver_dinero"
    reservas = (
        Reserva.objects
        .filter(estado=Reserva.Estado.DEVOLVER_DINERO)
        .select_related("id_usuario", "id_turno")
        .order_by("-fecha_reserva")
    )
    #lista de certificados pendientes que tienen estado "pendiente"
    certificados = (
        CertificadoMedico.objects
        .filter(estado=CertificadoMedico.Estado.PENDIENTE)
        .select_related("reserva__id_usuario", "reserva__id_turno")
        .order_by("-fecha_envio")
    )
    #lista de reservas que tienen estado "devolver_dinero" y no estan esperando a que le aprueben el certificado
    reservas_sin_certificado = reservas.exclude(id__in=certificados.values_list("reserva_id", flat=True))
    return TemplateResponse(request, "classes/lista_devoluciones.html", {"reservas": reservas_sin_certificado})

@login_required
@require_POST
def resolver_devolver_dinero(request, pk):
    if not (request.user.es_dueno or request.user.es_secretario):
        messages.error(request, "No tenés permisos para realizar esta acción.")
        return redirect("home")

    reserva = get_object_or_404(
        Reserva,
        pk=pk,
        estado=Reserva.Estado.DEVOLVER_DINERO
    )



    reserva.estado = Reserva.Estado.DINERO_DEVUELTO
    reserva.save()
    messages.success(request, f"Se aprobó la devolución de dinero para {reserva.id_usuario.nombre_completo}.")

    return redirect("turnos:devolver_dinero")

@login_required
@require_POST
def resolver_certificado(request, pk):
    if not (request.user.es_dueno):
        messages.error(request, "No tenés permisos para realizar esta acción.")
        return redirect("home")

    certificado = get_object_or_404(
        CertificadoMedico, pk=pk, estado=CertificadoMedico.Estado.PENDIENTE
    )
    accion = request.POST.get("accion")

    if accion == "validar":
        certificado.estado         = CertificadoMedico.Estado.VALIDADO
        certificado.revisado_por   = request.user
        certificado.fecha_revision = timezone.now()
        
        reserva = certificado.reserva
        
        if reserva.estado == Reserva.Estado.DEVOLVER_DINERO:
            messages.success(request, f"Certificado validado. Apruebe la devolución de dinero para {reserva.id_usuario.nombre_completo}.")
        else:
            usuario = certificado.reserva.id_usuario
            usuario.saldo_a_favor += certificado.reserva.id_turno.get_costo_clase
            usuario.save(update_fields=["saldo_a_favor"])
            messages.success(request, f"Certificado validado. Se le otorgó saldo a favor a {usuario.nombre_completo}.")
        certificado.save()

    elif accion == "rechazar":
        certificado.estado         = CertificadoMedico.Estado.RECHAZADO
        certificado.revisado_por   = request.user
        certificado.fecha_revision = timezone.now()
        certificado.save()
        messages.info(request, "Certificado rechazado. No se otorgó saldo a favor.")

    else:
        messages.error(request, "Acción no reconocida.")

    return redirect("turnos:lista_certificados")
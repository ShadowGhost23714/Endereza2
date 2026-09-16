from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views import View
import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from apps.classes.models import Turno, Reserva

User = get_user_model()

def home(request):
    hoy = timezone.localdate()
    ahora = timezone.localtime()

    turnos_qs = (
        Turno.objects
        .filter(
            fecha__gte=hoy,
            fecha__lte=hoy + timedelta(days=60),
        )
        .annotate(
            n_reservados=Count(
                "reservas",
                filter=Q(reservas__estado=Reserva.Estado.RESERVADO)
                     | Q(reservas__estado=Reserva.Estado.PAGO),
            )
        )
        .order_by("fecha", "hora_inicio")
    )

    mis_turnos_ids = set()
    if request.user.is_authenticated:
        mis_turnos_ids = set(
            Reserva.objects
            .filter(
                id_usuario=request.user,
                estado__in=[Reserva.Estado.RESERVADO, Reserva.Estado.PAGO],
            )
            .values_list("id_turno_id", flat=True)
        )

    clases_json = {}
    proximas_clases = []

    for turno in turnos_qs:
        key = str(turno.fecha)
        libres = turno.cupo - turno.n_reservados
        turno_del_dia = "Turno mañana" if turno.hora_inicio.hour < 14 else "Turno tarde"

        turno_dt = timezone.make_aware(
            timezone.datetime.combine(turno.fecha, turno.hora_inicio)
        )

        data = {
            "pk":                turno.pk,
            "actividad":         turno.get_actividad_display(),
            "hora":              turno.hora_inicio.strftime("%H:%M"),
            "hora_fin":          turno.hora_fin.strftime("%H:%M"),
            "cupo":              turno.cupo,
            "reservados":        turno.n_reservados,
            "cupos_disponibles": libres,
            "precio":            float(turno.precio),
            "estado": (
                "lleno"      if libres <= 0 else
                "pocos"      if libres <= max(turno.cupo // 4, 2) else
                "disponible"
            ),
            "reservado_por_mi": turno.pk in mis_turnos_ids,
            "turno_del_dia":    turno_del_dia,
        }

        clases_json.setdefault(key, []).append(data)

        if turno_dt > ahora and len(proximas_clases) < 5:
            proximas_clases.append(data)

    proximo_turno  = None
    clases_a_favor = 0
    pago_pendiente = None

    if request.user.is_authenticated:
        proxima_reserva = (
            Reserva.objects
            .filter(
                id_usuario=request.user,
                estado__in=[Reserva.Estado.RESERVADO, Reserva.Estado.PAGO],
                id_turno__fecha__gte=hoy,
            )
            .select_related("id_turno")
            .order_by("id_turno__fecha", "id_turno__hora_inicio")
            .first()
        )
        proximo_turno  = proxima_reserva.id_turno if proxima_reserva else None
        clases_a_favor = getattr(request.user, "clases_a_favor", 0)

        if Reserva.objects.filter(
            id_usuario=request.user,
            estado=Reserva.Estado.RESERVADO,
            id_turno__fecha__gte=hoy,
        ).exists():
            pago_pendiente = {"mensaje": "Tenés turnos sin pagar"}

    return render(request, 'core/index.html', {
        "clases_json":     json.dumps(clases_json, ensure_ascii=False),
        "proximas_clases": proximas_clases,
        "proximo_turno":   proximo_turno,
        "clases_a_favor":  clases_a_favor,
        "pago_pendiente":  pago_pendiente,
    })


def profile(request):
    return render(request, 'profile.html')


def dueño(request):
    usuarios = User.objects.all()
    return render(request, 'core/dueño.html', {'usuarios': usuarios})


def secretario(request):
    usuarios = User.objects.all()
    return render(request, 'turnos_view/turnos_del_dia.html', {'usuarios': usuarios})


class HomeRouterView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return dueño(request)
        if request.user.is_authenticated and request.user.es_secretario:
            return secretario(request)
        return home(request)
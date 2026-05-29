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
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {'usuarios': usuarios})

def profile(request):
    return render(request, 'profile.html')

def turnos(request):
    return render(request, 'turnos.html')

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
        else:
            return home(request)


# Vista principal con el calendario y resumen de reservas
def home(request):
    hoy = timezone.localdate()

    # ─────────────────────────────────────────────────────────
    # CALENDARIO — turnos de los próximos 60 días
    # ─────────────────────────────────────────────────────────
    turnos_qs = (
        Turno.objects
        .filter(
            fecha__gte=hoy,
            fecha__lte=hoy + timedelta(days=60),
        )
        # Contamos cuántas reservas activas (no canceladas) tiene cada turno
        .annotate(
            n_reservados=Count(
                "reservas",
                filter=Q(reservas__estado=Reserva.Estado.RESERVADO)
                     | Q(reservas__estado=Reserva.Estado.PAGO),
            )
        )
        .order_by("fecha", "hora_inicio")
    )

    # IDs de turnos que ya reservó el usuario actual
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

    # Construimos el dict { "YYYY-MM-DD": [ {...}, ... ] }
    # que el JS del calendario consume directamente
    clases_json = {}
    for turno in turnos_qs:
        key = str(turno.fecha)              # "2026-05-27"
        libres = turno.cupo - turno.n_reservados

        clases_json.setdefault(key, []).append({
            "pk":              turno.pk,
            "actividad":       turno.get_actividad_display(),  # "Tren inferior" etc.
            "hora":            turno.hora_inicio.strftime("%H:%M"),
            "hora_fin":        turno.hora_fin.strftime("%H:%M"),
            "cupo":            turno.cupo,
            "reservados":      turno.n_reservados,
            "libres":          libres,
            "precio":          float(turno.precio),
            # Estado para la barra de color: disponible / pocos / lleno
            "estado": (
                "lleno"      if libres <= 0 else
                "pocos"      if libres <= max(turno.cupo // 4, 2) else
                "disponible"
            ),
            # Si el usuario ya tiene este turno reservado
            "reservado_por_mi": turno.pk in mis_turnos_ids,
        })

    # ─────────────────────────────────────────────────────────
    # CARDS DE RESUMEN (solo para usuarios autenticados)
    # ─────────────────────────────────────────────────────────
    proximo_turno  = None
    clases_a_favor = 0
    pago_pendiente = None

    if request.user.is_authenticated:
        # Próximo turno reservado
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
        proximo_turno = proxima_reserva.id_turno if proxima_reserva else None

        # Clases a favor: reservas canceladas con clase a favor pendiente
        # (ajustá según cómo lo implementes en tu modelo)
        clases_a_favor = getattr(request.user, "clases_a_favor", 0)

        # Pago pendiente: reservas en estado RESERVADO (aún sin pagar)
        tiene_pago_pendiente = Reserva.objects.filter(
            id_usuario=request.user,
            estado=Reserva.Estado.RESERVADO,
            id_turno__fecha__gte=hoy,
        ).exists()

        if tiene_pago_pendiente:
            pago_pendiente = {
                "mensaje": "Tenés turnos sin pagar",
            }

    # ─────────────────────────────────────────────────────────
    # CONTEXTO PARA EL TEMPLATE
    # ─────────────────────────────────────────────────────────
    return render(request, 'core/index.html', {
        # JSON para el calendario JS
        "clases_json": json.dumps(clases_json, ensure_ascii=False),

        # Para la tabla de invitados (hoy, sin JS)
        "clases_hoy": clases_json.get(str(hoy), []),

        # Cards de resumen
        "proximo_turno":  proximo_turno,
        "clases_a_favor": clases_a_favor,
        "pago_pendiente": pago_pendiente,
    })
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import time as time_type
from django.views import View
from django.http import JsonResponse
from datetime import date as date_type
import mercadopago
from apps.classes.models import Reserva, Turno
from config import settings
from .models import Pago
from django.utils import timezone


class SecretarioRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_staff or user.es_secretario
        
class FiltrarTurnosView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        fecha_str = request.POST.get("fecha")
        actividad = request.POST.get("actividad")
        hora_str  = request.POST.get("hora", "")  # opcional

        try:
            fecha = date_type.fromisoformat(fecha_str)
        except (ValueError, TypeError):
            fecha = timezone.localdate()

        # Filtro base
        filtro = {"fecha": fecha, "actividad": actividad}

        # Si se eligió un horario, lo agregamos al filtro
        if hora_str:
            try:
                from datetime import time as time_type
                h = int(hora_str[:2])
                filtro["hora_inicio"] = time_type(h, 0)
            except (ValueError, IndexError):
                pass

        turnos = Turno.objects.filter(**filtro)

        if not turnos.exists():
            return JsonResponse({"reservas": []})

        reservas = (
            Reserva.objects.filter(id_turno__in=turnos)
            .exclude(estado=Reserva.Estado.CANCELADO)
            .select_related("id_usuario", "id_turno")
        )

        data = []
        for r in reservas:
            es_pasado = r.id_turno.fecha < timezone.localdate()
            data.append({
                "id":           r.pk,
                "nombre":       r.id_usuario.get_full_name() or r.id_usuario.username,
                "dni":          getattr(r.id_usuario, "dni", "—"),
                "estado":       r.estado,
                "hora":         r.id_turno.hora_inicio.strftime("%H:%M"),
                "ya_pagado":    r.estado == Reserva.Estado.PAGO,
                "recepcionado": r.recepcionado,
                "es_pasado":    r.id_turno.fecha < timezone.localdate(),
            })
        return JsonResponse({"reservas": data})


class CobrarTurnoView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        reserva_id  = request.POST.get("reserva_id")
        metodo_pago = request.POST.get("metodo_pago")
        try:
            reserva = Reserva.objects.get(pk=reserva_id, estado=Reserva.Estado.RESERVADO)
        except Reserva.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Reserva no encontrada o ya procesada."})
        if hasattr(reserva, "pago"):
            return JsonResponse({"ok": False, "error": "Esta reserva ya tiene un pago registrado."})
        with transaction.atomic():
            Pago.objects.create(
                reserva=reserva,
                metodo_pago=metodo_pago,
                registrado_por=request.user,
            )
            reserva.estado = Reserva.Estado.PAGO
            reserva.recepcionado = True
            reserva.save(update_fields=["estado", "recepcionado"])
        return JsonResponse({"ok": True, "mensaje": "Pago registrado correctamente."})


class CancelarTurnoView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        reserva_id = request.POST.get("reserva_id")
        try:
            reserva = Reserva.objects.get(pk=reserva_id)
        except Reserva.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Reserva no encontrada."})
        with transaction.atomic():
            reserva.estado = Reserva.Estado.CANCELADO
            reserva.save(update_fields=["estado"])
        return JsonResponse({"ok": True, "mensaje": "Turno cancelado correctamente."})
    
class RecepcionarTurnoView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        reserva_id = request.POST.get("reserva_id")
        try:
            reserva = Reserva.objects.get(pk=reserva_id, estado=Reserva.Estado.PAGO)
        except Reserva.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Reserva no encontrada o no está paga."})
        with transaction.atomic():
            reserva.recepcionado = True
            reserva.save(update_fields=["recepcionado"])
        return JsonResponse({"ok": True, "mensaje": "Paciente recepcionado correctamente."})

class CancelarRecepcionView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        reserva_id = request.POST.get("reserva_id")
        try:
            reserva = Reserva.objects.get(pk=reserva_id, estado=Reserva.Estado.PAGO, recepcionado=True)
        except Reserva.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Reserva no encontrada o no está recepcionada."})
        with transaction.atomic():
            reserva.recepcionado = False
            reserva.save(update_fields=["recepcionado"])
        return JsonResponse({"ok": True, "mensaje": "Recepción cancelada correctamente."})

class BuscarPacientePorDniView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        dni      = request.GET.get("dni", "").strip()
        turno_id = request.GET.get("turno_id", "")

        if not dni:
            return JsonResponse({"encontrado": False})
        try:
            usuario = User.objects.get(dni=dni)

            ya_reservado    = False
            conflicto_horario = False

            if turno_id:
                ya_reservado = Reserva.objects.filter(
                    id_usuario=usuario,
                    id_turno_id=turno_id
                ).exclude(estado=Reserva.Estado.CANCELADO).exists()

                if not ya_reservado:
                    try:
                        turno = Turno.objects.get(pk=turno_id)
                        conflicto_horario = Reserva.objects.filter(
                            id_usuario=usuario,
                            id_turno__fecha=turno.fecha,
                            id_turno__hora_inicio=turno.hora_inicio,
                        ).exclude(estado=Reserva.Estado.CANCELADO).exists()
                    except Turno.DoesNotExist:
                        pass

            return JsonResponse({
                "encontrado":       True,
                "id":               usuario.pk,
                "nombre":           usuario.get_full_name() or usuario.email,
                "ya_reservado":     ya_reservado,
                "conflicto_horario": conflicto_horario,
            })
        except User.DoesNotExist:
            return JsonResponse({"encontrado": False})


class TurnoEspontaneoView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def get(self, request):
        ahora = timezone.localtime()
        hoy   = ahora.date()
        hora_actual = ahora.time()
        turnos = (
            Turno.objects.filter(fecha=hoy, hora_inicio__gt=hora_actual)
            .order_by("hora_inicio", "actividad")
        )
        data = []
        for t in turnos:
            if t.tiene_cupo():
                data.append({
                    "id":    t.pk,
                    "label": f"{t.get_actividad_display()} — {t.hora_inicio.strftime('%H:%M')} a {t.hora_fin.strftime('%H:%M')}",
                    "cupos": t.cupos_disponibles(),
                })
        return JsonResponse({"turnos": data})

    def post(self, request):
        turno_id    = request.POST.get("turno_id")
        usuario_id  = request.POST.get("usuario_id")
        metodo_pago = request.POST.get("metodo_pago")

        try:
            turno   = Turno.objects.get(pk=turno_id)
            from django.contrib.auth import get_user_model
            User    = get_user_model()
            usuario = User.objects.get(pk=usuario_id)
        except Exception:
            return JsonResponse({"ok": False, "error": "Turno o paciente no encontrado."})

        if not turno.tiene_cupo():
            return JsonResponse({"ok": False, "error": "El turno no tiene cupos disponibles."})

        if Reserva.objects.filter(id_usuario=usuario, id_turno=turno).exists():
            return JsonResponse({"ok": False, "error": "El paciente ya tiene una reserva para este turno."})

        conflicto = Reserva.objects.filter(
            id_usuario=usuario,
            id_turno__fecha=turno.fecha,
            id_turno__hora_inicio=turno.hora_inicio,
        ).exclude(estado=Reserva.Estado.CANCELADO).exists()

        if conflicto:
            return JsonResponse({"ok": False, "error": "El paciente ya tiene un turno reservado en ese día y horario."})

        with transaction.atomic():
            reserva = Reserva.objects.create(
                id_usuario   = usuario,
                id_turno     = turno,
                estado       = Reserva.Estado.PAGO,
                recepcionado = True,
            )
            Pago.objects.create(
                reserva        = reserva,
                metodo_pago    = metodo_pago,
                registrado_por = request.user,
            )

        return JsonResponse({"ok": True, "mensaje": f"Turno registrado y cobrado correctamente para {usuario.get_full_name()}."})
    
class ClasesPorActividadView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def get(self, request):
        actividad = request.GET.get("actividad", "")
        ahora = timezone.localtime()
        hoy   = ahora.date()
        hora_actual = ahora.time()
        turnos = (
            Turno.objects.filter(actividad=actividad, fecha__gt=hoy)
            | Turno.objects.filter(actividad=actividad, fecha=hoy, hora_inicio__gt=hora_actual)
        ).order_by("fecha", "hora_inicio")
        data = []
        for t in turnos:
            if t.tiene_cupo():
                data.append({
                    "id":    t.pk,
                    "label": f"{t.fecha.strftime('%d/%m/%Y')} — {t.hora_inicio.strftime('%H:%M')} a {t.hora_fin.strftime('%H:%M')} ({t.cupos_disponibles()} cupos)",
                })
        return JsonResponse({"turnos": data})


class NuevaReservaView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        turno_id     = request.POST.get("turno_id")
        usuario_id   = request.POST.get("usuario_id")
        cobrar_ahora = request.POST.get("cobrar_ahora") == "true"
        metodo_pago  = request.POST.get("metodo_pago", "")

        try:
            turno   = Turno.objects.get(pk=turno_id)
            from django.contrib.auth import get_user_model
            User    = get_user_model()
            usuario = User.objects.get(pk=usuario_id)
        except Exception:
            return JsonResponse({"ok": False, "error": "Turno o paciente no encontrado."})

        if not turno.tiene_cupo():
            return JsonResponse({"ok": False, "error": "El turno no tiene cupos disponibles."})

        if Reserva.objects.filter(id_usuario=usuario, id_turno=turno).exists():
            return JsonResponse({"ok": False, "error": "El paciente ya tiene una reserva para este turno."})

        conflicto = Reserva.objects.filter(
            id_usuario=usuario,
            id_turno__fecha=turno.fecha,
            id_turno__hora_inicio=turno.hora_inicio,
        ).exclude(estado=Reserva.Estado.CANCELADO).exists()

        if conflicto:
            return JsonResponse({"ok": False, "error": "El paciente ya tiene un turno reservado en ese día y horario."})

        with transaction.atomic():
            if cobrar_ahora:
                reserva = Reserva.objects.create(
                    id_usuario   = usuario,
                    id_turno     = turno,
                    estado       = Reserva.Estado.PAGO,
                    recepcionado = False,
                )
                Pago.objects.create(
                    reserva        = reserva,
                    metodo_pago    = metodo_pago,
                    registrado_por = request.user,
                )
                mensaje = f"Reserva creada y cobrada correctamente para {usuario.get_full_name()}."
            else:
                reserva = Reserva.objects.create(
                    id_usuario = usuario,
                    id_turno   = turno,
                    estado     = Reserva.Estado.RESERVADO,
                )
                mensaje = f"Reserva creada correctamente para {usuario.get_full_name()}."

        return JsonResponse({"ok": True, "mensaje": mensaje})
    
class RegistrarPacienteView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        from django.contrib.auth import get_user_model
        import secrets
        import string
        User = get_user_model()

        nombre          = request.POST.get("nombre", "").strip()
        apellido        = request.POST.get("apellido", "").strip()
        dni             = request.POST.get("dni", "").strip()
        fecha_nacimiento = request.POST.get("fecha_nacimiento", "").strip()
        email           = request.POST.get("email", "").strip()

        # Validaciones básicas
        if not all([nombre, apellido, dni, email]):
            return JsonResponse({"ok": False, "error": "Todos los campos son obligatorios."})

        if User.objects.filter(email=email).exists():
            return JsonResponse({"ok": False, "error": "Ya existe un usuario con ese email."})

        if User.objects.filter(dni=dni).exists():
            return JsonResponse({"ok": False, "error": "Ya existe un usuario con ese DNI."})

        # Generar contraseña aleatoria
        caracteres = string.ascii_letters + string.digits
        password   = "".join(secrets.choice(caracteres) for _ in range(12))

        try:
            from datetime import date as date_type_cls
            fn = date_type_cls.fromisoformat(fecha_nacimiento) if fecha_nacimiento else None
        except ValueError:
            fn = None

        with transaction.atomic():
            usuario = User.objects.create_user(
                email            = email,
                password         = password,
                first_name       = nombre,
                last_name        = apellido,
                dni              = dni,
                fecha_nacimiento = fn,
                tipo             = "cliente",
            )

        # Simulación de envío de email
        print(f"[SIMULACIÓN EMAIL] Para: {email} | Contraseña temporal: {password}")

        return JsonResponse({
            "ok":     True,
            "id":     usuario.pk,
            "nombre": usuario.get_full_name(),
            "mensaje": f"Paciente {usuario.get_full_name()} registrado correctamente.",
        })
class NuevoAbonadoView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    def post(self, request):
        from django.contrib.auth import get_user_model
        from datetime import date
        User = get_user_model()

        dni = request.POST.get("dni", "").strip()

        if not dni:
            return JsonResponse({"ok": False, "error": "Ingresá un DNI."})

        try:
            usuario = User.objects.get(dni=dni)
        except User.DoesNotExist:
            return JsonResponse({"ok": False, "error": "No existe un paciente con ese DNI."})

        if usuario.abono_activo:
            return JsonResponse({"ok": False, "error": "Este paciente ya tiene un abono activo."})

        # Calcular vencimiento: día 11 del próximo mes
        hoy = date.today()
        vencimiento = date(hoy.year, hoy.month, 11)
        if hoy.month == 12:
            vencimiento = date(hoy.year + 1, 1, 11)
        else:
            vencimiento = date(hoy.year, hoy.month + 1, 11)

        with transaction.atomic():
            usuario.tiene_abono_mensual = True
            usuario.abono_vencimiento   = vencimiento
            usuario.save(update_fields=["tiene_abono_mensual", "abono_vencimiento"])

        return JsonResponse({
            "ok":      True,
            "mensaje": f"Abono registrado para {usuario.get_full_name()}. Vence el {vencimiento.strftime('%d/%m/%Y')}.",
        })                            
    
class VerificarQRView(LoginRequiredMixin, SecretarioRequiredMixin, View):
    """
    Verifica el token de un QR escaneado y devuelve qué pantalla
    debe abrir el frontend, según las reglas de negocio:

    - invalido        -> el token no corresponde a ninguna reserva válida
    - fecha_invalida   -> el QR es de un turno que no es el de hoy
    - fuera_de_horario -> es de hoy, pero ya pasó más de 1 hora desde el inicio
    - ya_utilizado     -> la reserva ya fue recepcionada antes
    - deuda_abono      -> el cliente tiene abono mensual vencido
    - no_pago          -> la reserva no está paga (hay que cobrar)
    - pago_confirmado  -> la reserva está paga (hay que recepcionar)
    """
    def post(self, request):
        token = request.POST.get("token", "").strip()

        try:
            reserva = (
                Reserva.objects
                .select_related("id_turno", "id_usuario")
                .get(qr_token=token)
            )
        except (Reserva.DoesNotExist, ValidationError, ValueError):
            return JsonResponse({
                "ok": False,
                "tipo": "invalido",
                "error": "El QR escaneado no pertenece a una reserva.",
            })

        if reserva.estado in (Reserva.Estado.CANCELADO, Reserva.Estado.LISTA_ESPERA):
            return JsonResponse({
                "ok": False,
                "tipo": "invalido",
                "error": "Este QR no corresponde a una reserva válida.",
            })

        if reserva.id_turno.fecha != timezone.localdate():
            return JsonResponse({
                "ok": False,
                "tipo": "fecha_invalida",
                "error": "El QR escaneado no pertenece a una reserva para la fecha actual.",
            })

        if timezone.now() > reserva.id_turno.limite_recepcion:
            return JsonResponse({
                "ok": False,
                "tipo": "fuera_de_horario",
                "error": "El QR escaneado corresponde a un turno fuera del horario habilitado para recepción.",
            })

        if reserva.recepcionado:
            return JsonResponse({
                "ok": False,
                "tipo": "ya_utilizado",
                "error": "El QR escaneado ya fue utilizado anteriormente.",
            })

        usuario = reserva.id_usuario
        if usuario.tiene_abono_mensual and not usuario.abono_activo:
            return JsonResponse({
                "ok": False,
                "tipo": "deuda_abono",
                "error": "El QR escaneado pertenece a un cliente con deuda de abono mensual.",
            })

        reserva_data = {
            "id":       reserva.pk,
            "nombre":   usuario.get_full_name() or usuario.email,
            "dni":      getattr(usuario, "dni", "—"),
            "hora":     reserva.id_turno.hora_inicio.strftime("%H:%M"),
            "actividad": reserva.id_turno.get_actividad_display(),
        }

        # Cliente con abono mensual activo: la clase ya está cubierta por el
        # abono, no corresponde pedirle que pague esta reserva puntual.
        if usuario.tiene_abono_mensual and usuario.abono_activo:
            vencimiento = usuario.abono_vencimiento.strftime("%d/%m/%Y")
            return JsonResponse({
                "ok":      True,
                "tipo":    "pago_confirmado",
                "mensaje": f"El abono se encuentra activo hasta el día {vencimiento}, confirme recepción.",
                "reserva": reserva_data,
            })

        if reserva.estado != Reserva.Estado.PAGO:
            return JsonResponse({
                "ok":      True,
                "tipo":    "no_pago",
                "mensaje": "Reserva no está paga, registre el pago para avanzar.",
                "reserva": reserva_data,
            })

        return JsonResponse({
            "ok":      True,
            "tipo":    "pago_confirmado",
            "mensaje": "Reserva paga, confirme recepción.",
            "reserva": reserva_data,
        })    


# Vistas para reservas online y MercadoPago

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from apps.classes.models import Turno, Reserva
from .services import crear_preferencia, MercadoPagoConnectionError, sincronizar_pago  
import json, logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


# Vista para reservar una clase online y redirigir a MercadoPago
@login_required
@require_POST
def reservar_online(request, turno_id):
    turno = get_object_or_404(Turno, pk=turno_id)

    if not turno.tiene_cupo():
        messages.error(request, "No hay cupos disponibles para este turno.")
        return redirect("classes:listar_clases")

    reserva, created = Reserva.objects.get_or_create(
        id_usuario=request.user,
        id_turno=turno,
        defaults={"estado": Reserva.Estado.RESERVADO}
    )

    if not created and reserva.estado == Reserva.Estado.PAGO:
        messages.info(request, "Ya tenés esta clase pagada.")
        return redirect("classes:listar_clases")

    # --- Escenario 2: error de conexión con la API ---
    try:
        preferencia = crear_preferencia(reserva, request)
    except MercadoPagoConnectionError:
        messages.error(request, "No se pudo conectar a Mercado Pago. Intente más tarde")
        return redirect("turnos:listar_clases")

    pago, _ = Pago.objects.get_or_create(reserva=reserva)
    pago.metodo_pago   = Pago.MetodoPago.MERCADO_PAGO
    pago.preference_id = preferencia["id"]
    pago.monto         = reserva.id_turno.precio
    pago.estado        = Pago.Estado.PENDIENTE
    pago.save()

    # --- Escenario 1: redirige al pago ---
    return redirect(preferencia["init_point"])

# Vistas para manejar las redirecciones de MercadoPago después del pago
def pago_exito(request):
    payment_id = request.GET.get("payment_id")
    external_reference = request.GET.get("external_reference")
    pago = sincronizar_pago(payment_id, external_reference)

    # --- Escenario 1: pago exitoso ---
    if pago and pago.esta_aprobado:
        messages.success(request, "Reserva pagada")
    else:
        messages.error(request, "Hubo problemas para realizar el pago")

    return redirect("turnos:listar_clases")


def pago_error(request):
    payment_id = request.GET.get("payment_id")
    external_reference = request.GET.get("external_reference")
    sincronizar_pago(payment_id, external_reference)

    # --- Escenario 3: pago fallido en MP ---
    messages.error(request, "Hubo problemas para realizar el pago")
    return redirect("turnos:listar_clases")


def pago_pendiente(request):
    payment_id = request.GET.get("payment_id")
    external_reference = request.GET.get("external_reference")
    sincronizar_pago(payment_id, external_reference)

    messages.info(request, "Tu pago está pendiente de confirmación")
    return redirect("turnos:listar_clases")


# Configuración de logging para el webhook
logger = logging.getLogger(__name__)
@csrf_exempt
@require_POST
def webhook(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    if data.get("type") != "payment":
        return HttpResponse(status=200)

    payment_id = str(data.get("data", {}).get("id", ""))
    if not payment_id:
        return HttpResponse(status=400)

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    mp_pago = sdk.payment().get(payment_id)["response"]

    reserva_id = mp_pago.get("external_reference")
    estado_mp  = mp_pago.get("status")

    ESTADOS = {
        "approved":   Pago.Estado.APROBADO,
        "rejected":   Pago.Estado.RECHAZADO,
        "pending":    Pago.Estado.PENDIENTE,
        "in_process": Pago.Estado.EN_PROCESO,
        "cancelled":  Pago.Estado.CANCELADO,
    }

    try:
        pago = Pago.objects.get(reserva__id=reserva_id)
        pago.payment_id = payment_id
        pago.estado     = ESTADOS.get(estado_mp, Pago.Estado.PENDIENTE)
        pago.save()

        if pago.esta_aprobado:
            pago.reserva.estado = Reserva.Estado.PAGO
            pago.reserva.save()
    except Pago.DoesNotExist:
        logger.warning(f"Webhook: no se encontró pago para reserva {reserva_id}")

    return HttpResponse(status=200)

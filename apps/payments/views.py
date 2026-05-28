from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.db import transaction
from datetime import time as time_type
from django.views import View
from django.http import JsonResponse
from datetime import date as date_type
from apps.classes.models import Reserva, Turno
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
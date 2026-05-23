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


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
        
class FiltrarTurnosView(LoginRequiredMixin, StaffRequiredMixin, View):
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
            data.append({
                "id":        r.pk,
                "nombre":    r.id_usuario.get_full_name() or r.id_usuario.username,
                "dni":       getattr(r.id_usuario, "dni", "—"),
                "estado":    r.estado,
                "hora":      r.id_turno.hora_inicio.strftime("%H:%M"),
                "ya_pagado": r.estado == Reserva.Estado.PAGO,
            })
        return JsonResponse({"reservas": data})


class CobrarTurnoView(LoginRequiredMixin, StaffRequiredMixin, View):
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
            reserva.save(update_fields=["estado"])
        return JsonResponse({"ok": True, "mensaje": "Pago registrado correctamente."})


class CancelarTurnoView(LoginRequiredMixin, StaffRequiredMixin, View):
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
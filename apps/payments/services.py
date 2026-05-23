from django.db import transaction
from django.shortcuts import get_object_or_404
from classes.models import Reserva
from .models import Pago

def procesar_pago_presencial(reserva_id, monto, metodo_pago="efectivo"):
    with transaction.atomic():
        # 1. Traer la reserva específica del paciente
        reserva = get_object_or_404(Reserva, id=reserva_id)

        # 2. Validar que cumpla la regla de negocio (aún pendiente de pago)
        if reserva.estado != Reserva.Estado.RESERVADO:
            raise ValueError("Esta reserva ya se encuentra paga o fue cancelada.")

        # 3. Crear el comprobante de pago
        nuevo_pago = Pago.objects.create(
            reserva=reserva,
            monto=monto,
            metodo=metodo_pago
        )

        # 4. Actualizar el estado de la reserva
        reserva.estado = Reserva.Estado.PAGO
        reserva.save()

        return nuevo_pago
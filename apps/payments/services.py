from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.classes.models import Reserva
from .models import Pago
import mercadopago
from django.conf import settings

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
    

# Función para crear la preferencia de pago en MercadoPago
def crear_preferencia(reserva, request):
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    base_url = "https://extinct-stem-sporting.ngrok-free.dev"

    preference_data = {
        "items": [{
            "id": str(reserva.id),
            "title": f"Reserva #{reserva.id} — {reserva.id_turno.get_actividad_display()}",
            "quantity": 1,
            "unit_price": float(reserva.id_turno.precio),
            "currency_id": "ARS",
        }],
        "back_urls": {
            "success": f"{base_url}/pagos/exito/",
            "failure": f"{base_url}/pagos/error/",
            "pending": f"{base_url}/pagos/pendiente/",
        },
        "auto_return": "approved",
        "external_reference": str(reserva.id),
        "notification_url": request.build_absolute_uri("/pagos/webhook/"),
    }

    response = sdk.preference().create(preference_data)
    print("RESPUESTA COMPLETA DE MP:", response)  # ← agregar esto
    return response["response"]
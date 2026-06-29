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
    

# Excepción personalizada para errores de conexión con MercadoPago
class MercadoPagoConnectionError(Exception):
    """Se lanza cuando falla la conexión con la API de MercadoPago."""
    pass

# Función para crear la preferencia de pago en MercadoPago
def crear_preferencia(reserva, request):
    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    base_url = "https://extinct-stem-sporting.ngrok-free.dev"
    preference_data = {
        # Detalles del producto/servicio a pagar
        "items": [{
            "id": str(reserva.id),
            "title": f"Reserva #{reserva.id} — {reserva.id_turno.get_actividad_display()}",
            "quantity": 1,
            "unit_price": float(reserva.id_turno.precio),
            "currency_id": "ARS",
        }],
        # URLs de redirección después del pago
        "back_urls": {
            "success": f"{base_url}/pagos/exito/",
            "failure": f"{base_url}/pagos/error/",
            "pending": f"{base_url}/pagos/pendiente/",
        },
        "auto_return": "approved",
        "external_reference": str(reserva.id),
        "notification_url": f"{base_url}/pagos/webhook/",
    }

    try:
        response = sdk.preference().create(preference_data)
    except Exception as e:
        # Falla de red, timeout, DNS, etc. — la API ni respondió
        raise MercadoPagoConnectionError(str(e))

    print("RESPUESTA COMPLETA DE MP:", response)

    # La API respondió, pero con un error (credenciales inválidas, datos mal armados, etc.)
    if response.get("status") not in (200, 201):
        raise MercadoPagoConnectionError(response.get("response", {}).get("message", "Error desconocido de MercadoPago"))

    return response["response"]

# --- Función compartida para sincronizar el estado del pago con MP ---
ESTADOS_MP = {
    "approved":   Pago.Estado.APROBADO,
    "rejected":   Pago.Estado.RECHAZADO,
    "pending":    Pago.Estado.PENDIENTE,
    "in_process": Pago.Estado.EN_PROCESO,
    "cancelled":  Pago.Estado.CANCELADO,
}


def sincronizar_pago(payment_id, external_reference):
    """Consulta el estado real a MP y actualiza Pago + Reserva."""
    if not payment_id or not external_reference:
        return None

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
    mp_pago = sdk.payment().get(payment_id)["response"]
    estado_mp = mp_pago.get("status")

    try:
        pago = Pago.objects.get(reserva__id=external_reference)
        pago.payment_id = payment_id
        pago.estado = ESTADOS_MP.get(estado_mp, Pago.Estado.PENDIENTE)
        pago.save()

        if pago.esta_aprobado:
            pago.reserva.estado = Reserva.Estado.PAGO
            pago.reserva.save()

        return pago
    except Pago.DoesNotExist:
        return None
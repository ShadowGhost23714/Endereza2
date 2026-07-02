# apps/classes/emails.py
from django.core.mail import send_mail
from django.conf import settings

from apps.classes.models import Reserva

def obtener_primera_persona_en_lista_espera(turno):
    """Devuelve la primera persona en lista de espera para un turno dado."""
    #filtrar reservas que tengan el mismo turno y que estén en estado de lista de espera, ordenadas por fecha de creación
    reserva_lista_espera = Reserva.objects.filter(
        id_turno=turno,
        estado=Reserva.Estado.LISTA_ESPERA
    ).order_by('fecha_reserva').first()
    
    return reserva_lista_espera

def enviar_confirmacion_reserva(reserva):
    """Envía un email de confirmación al usuario cuando reserva una clase."""
    turno   = reserva.id_turno
    usuario = reserva.id_usuario

    asunto = f"Reserva confirmada — {turno.actividad} el {turno.fecha}"
    cuerpo = (
        f"Hola {usuario.first_name or usuario.username},\n\n"
        f"Tu reserva fue confirmada exitosamente.\n\n"
        f"  Actividad : {turno.actividad}\n"
        f"  Fecha     : {turno.fecha.strftime('%d/%m/%Y')}\n"
        f"  Horario   : {turno.hora_inicio.strftime('%H:%M')} – {turno.hora_fin.strftime('%H:%M')}\n"
        f"  Estado    : Reservado\n\n"
        f"Si necesitás cancelar, ingresá a tu cuenta en Endereza2.\n\n"
        f"¡Nos vemos pronto!\n"
        f"El equipo de Endereza2"
    )

    send_mail(
        subject      = asunto,
        message      = cuerpo,
        from_email   = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [usuario.email],
        fail_silently  = True,
    )


def enviar_confirmacion_lista_espera(reserva):
    """Envía un email informando que el usuario quedó en lista de espera."""
    turno   = reserva.id_turno
    usuario = reserva.id_usuario

    asunto = f"Lista de espera — {turno.actividad} el {turno.fecha}"
    cuerpo = (
        f"Hola {usuario.first_name or usuario.username},\n\n"
        f"El turno que elegiste no tiene cupos disponibles, pero te anotamos en la lista de espera.\n\n"
        f"  Actividad : {turno.actividad}\n"
        f"  Fecha     : {turno.fecha.strftime('%d/%m/%Y')}\n"
        f"  Horario   : {turno.hora_inicio.strftime('%H:%M')} – {turno.hora_fin.strftime('%H:%M')}\n"
        f"  Estado    : Lista de espera\n\n"
        f"Si se libera un cupo te avisamos automáticamente.\n\n"
        f"El equipo de Endereza2"
    )

    send_mail(
        subject      = asunto,
        message      = cuerpo,
        from_email   = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [usuario.email],
        fail_silently  = True,
    )

def enviar_confirmacion_lista_espera_por_cancelacion(reserva):
    """Envía un email informando que el usuario fue movido de la lista de espera a reserva activa."""
    turno   = reserva.id_turno
    usuario = reserva.id_usuario
    destino = obtener_primera_persona_en_lista_espera(turno)

    if not destino:
        return  # No hay nadie en lista de espera, no se envía ningún correo
    asunto = f"¡Cupo disponible! — {turno.actividad} el {turno.fecha}"
    cuerpo = (
        f"Hola {usuario.first_name or usuario.username},\n\n"
        f"¡Buenas noticias! Se liberó un cupo en el turno que estabas esperando.\n\n"
        f"  Actividad : {turno.actividad}\n"
        f"  Fecha     : {turno.fecha.strftime('%d/%m/%Y')}\n"
        f"  Horario   : {turno.hora_inicio.strftime('%H:%M')} – {turno.hora_fin.strftime('%H:%M')}\n"
        f"  Estado    : Reservado\n\n"
        f"Recordá que debés abonar en efectivo al llegar a la clase.\n\n"
        f"¡Nos vemos pronto!\n"
        f"El equipo de Endereza2"
    )

    send_mail(
        subject      = asunto,
        message      = cuerpo,
        from_email   = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [destino.id_usuario.email],
        fail_silently  = True,
    )
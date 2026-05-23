# apps/classes/emails.py
from django.core.mail import send_mail
from django.conf import settings


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
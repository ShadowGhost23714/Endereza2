from django.urls import path
from .views import (
    FiltrarTurnosView, CobrarTurnoView, CancelarTurnoView,
    RecepcionarTurnoView, CancelarRecepcionView,
    BuscarPacientePorDniView, TurnoEspontaneoView,
    ClasesPorActividadView, NuevaReservaView,RegistrarPacienteView,
    NuevoAbonadoView,VerificarQRView,
)
from . import views

app_name = "payments"

urlpatterns = [
    path("api/filtrar/",            FiltrarTurnosView.as_view(),       name="api_filtrar"),
    path("api/cobrar/",             CobrarTurnoView.as_view(),         name="api_cobrar"),
    path("api/cancelar/",           CancelarTurnoView.as_view(),       name="api_cancelar"),
    path("api/recepcionar/",        RecepcionarTurnoView.as_view(),    name="api_recepcionar"),
    path("api/cancelar-recepcion/", CancelarRecepcionView.as_view(),   name="api_cancelar_recepcion"),
    path("api/buscar-paciente/",    BuscarPacientePorDniView.as_view(),name="api_buscar_paciente"),
    path("api/turno-espontaneo/",   TurnoEspontaneoView.as_view(),     name="api_turno_espontaneo"),
    path("api/clases-por-actividad/", ClasesPorActividadView.as_view(), name="api_clases_por_actividad"),
    path("api/nueva-reserva/",      NuevaReservaView.as_view(),        name="api_nueva_reserva"),
    path("api/registrar-paciente/",  RegistrarPacienteView.as_view(),   name="api_registrar_paciente"),
    path("api/nuevo-abonado/",      NuevoAbonadoView.as_view(),        name="api_nuevo_abonado"),
    path("api/verificar-qr/",       VerificarQRView.as_view(),        name="api_verificar_qr"),

    # Rutas para pagos online con MercadoPago 
    path("reservar-online/<int:turno_id>/", views.reservar_online, name="reservar_online"),
    path("webhook/",      views.webhook,        name="webhook"),
    path("exito/",        views.pago_exito,      name="exito"),
    path("error/",        views.pago_error,      name="error"),
    path("pendiente/",    views.pago_pendiente,  name="pendiente"),
]
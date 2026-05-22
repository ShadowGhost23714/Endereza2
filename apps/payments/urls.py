from django.urls import path
from .views import FiltrarTurnosView, CobrarTurnoView, CancelarTurnoView, RecepcionarTurnoView, CancelarRecepcionView

app_name = "payments"

urlpatterns = [
    path("api/filtrar/",            FiltrarTurnosView.as_view(),      name="api_filtrar"),
    path("api/cobrar/",             CobrarTurnoView.as_view(),        name="api_cobrar"),
    path("api/cancelar/",           CancelarTurnoView.as_view(),      name="api_cancelar"),
    path("api/recepcionar/",        RecepcionarTurnoView.as_view(),   name="api_recepcionar"),
    path("api/cancelar-recepcion/", CancelarRecepcionView.as_view(),  name="api_cancelar_recepcion"),
]
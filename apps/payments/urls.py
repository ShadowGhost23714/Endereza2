from django.urls import path
from .views import FiltrarTurnosView, CobrarTurnoView, CancelarTurnoView

app_name = "payments"

urlpatterns = [
    path("api/filtrar/",  FiltrarTurnosView.as_view(), name="api_filtrar"),
    path("api/cobrar/",   CobrarTurnoView.as_view(),   name="api_cobrar"),
    path("api/cancelar/", CancelarTurnoView.as_view(), name="api_cancelar"),
]
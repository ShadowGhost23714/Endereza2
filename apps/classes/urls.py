from django.urls import path
from .views import MisClasesView, TurnoCreateView, TurnoListView, reservar_clase

app_name = "turnos"

urlpatterns = [
    path("", TurnoListView.as_view(), name="listar_clases"),
    path("reservar/<int:turno_id>/", reservar_clase, name="reservar_clase"),
    path("nuevo/", TurnoCreateView.as_view(), name="turno_create"),
    path("mis-clases/", MisClasesView.as_view(), name="mis_clases"),
]
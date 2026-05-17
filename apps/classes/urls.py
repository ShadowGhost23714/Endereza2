from django.urls import path
from .views import MisClasesView, TurnoCreateView

app_name = "turnos"

urlpatterns = [
    path("nuevo/", TurnoCreateView.as_view(), name="turno_create"),
    path("mis-clases/", MisClasesView.as_view(), name="mis_clases"),
]
from django.urls import path
from .views import TurnosDelDiaView

app_name = "turnos_view"

urlpatterns = [
    path("", TurnosDelDiaView.as_view(), name="turnos_del_dia"),
]
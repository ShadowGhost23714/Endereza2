from django.urls import path
from .views import TurnoCreateView

app_name = "turnos"

urlpatterns = [
    path("nuevo/", TurnoCreateView.as_view(), name="turno_create"),
    # Add turno_list, turno_detail, etc. here as needed.
]
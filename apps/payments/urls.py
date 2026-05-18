from django.urls import path
from .views import RegistrarPagoView

app_name = "payments"

urlpatterns = [
    path("registrar/", RegistrarPagoView.as_view(), name="registrar_pago"),
]
from django.urls import path
from .views import HistorialPagosView

app_name = "historial_pagos"

urlpatterns = [
    path("", HistorialPagosView.as_view(), name="historial"),
]

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [

    path("", views.home, name="home"),
    path("turnos/", views.turnos, name="turnos"),

]


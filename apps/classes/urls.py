# apps/classes/urls.py
from django.urls import path
from . import views

app_name = "turnos"

urlpatterns = [
    path("clases/",            views.TurnoListView.as_view(),    name="listar_clases"),
    path("crear/",             views.TurnoCreateView.as_view(),  name="turno_create"),
    path("mis-clases/",        views.MisClasesView.as_view(),    name="mis_clases"),
    path("reservas/",          views.ReservaListView.as_view(),  name="reserva_list"),
    path("reservar/<int:turno_id>/",       views.reservar_clase,         name="reservar_clase", kwargs={"efectivo": False}),
    path("efectivo/<int:turno_id>/",       views.reservar_clase,         name="reservar_efectivo", kwargs={"efectivo": True}),
    path("lista-espera/<int:turno_id>/",   views.anotarse_lista_espera,  name="lista_espera"),  # ← NUEVO
    path("eliminar-turno/<int:pk>/", views.TurnoDeleteView.as_view(),        name="turno_delete"),
]
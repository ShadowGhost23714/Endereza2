# profesores/urls.py

from django.urls import path

from .views import ProfesorCreateAjaxView, ProfesorCreateView, ProfesorListView, ProfesorDeleteView, ProfesorClasesAsignadasView

app_name = "profesores"

urlpatterns = [
    path("crear/",               ProfesorCreateView.as_view(), name="crear"),
    path("",                     ProfesorListView.as_view(),   name="lista"),
    path("<int:pk>/eliminar/",   ProfesorDeleteView.as_view(), name="eliminar"),
    path("<int:pk>/clases-asignadas/",    ProfesorClasesAsignadasView.as_view(), name="clases_asignadas"),
    path("crear-ajax/",                   ProfesorCreateAjaxView.as_view(),      name="crear_ajax"),
]
# profesores/urls.py

from django.urls import path

from .views import ProfesorCreateView, ProfesorListView, ProfesorDeleteView

app_name = "profesores"

urlpatterns = [
    path("crear/",               ProfesorCreateView.as_view(), name="crear"),
    path("",                     ProfesorListView.as_view(),   name="lista"),
    path("<int:pk>/eliminar/",   ProfesorDeleteView.as_view(), name="eliminar"),
]
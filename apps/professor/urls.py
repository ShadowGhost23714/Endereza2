# profesores/urls.py

from django.urls import path

from .views import ProfesorCreateView, ProfesorListView

app_name = "profesores"

urlpatterns = [
    path("nuevo/",   ProfesorCreateView.as_view(), name="crear"),
    path("",         ProfesorListView.as_view(),   name="lista"),
]
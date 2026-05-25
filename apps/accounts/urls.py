from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView, CustomPasswordChangeView
from django.contrib.auth import logout

app_name = "accounts"

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('secretario/', views.secretario, name='secretario'),
    path('secretario/lista/', views.lista_secretarios, name='lista_secretarios'),  # ← AGREGAR
    path('secretario/<int:pk>/eliminar/', views.eliminar_secretario, name='eliminar_secretario'),  # ← AGREGAR
    path('change_password/', CustomPasswordChangeView.as_view(), name="change_password")
]
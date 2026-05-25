from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView, CustomPasswordChangeView

app_name = "accounts"

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('secretario/nuevo/', views.secretario, name='secretario'),
    path('secretario/lista/', views.lista_secretarios, name='lista_secretarios'),
    path('secretario/<int:pk>/eliminar/', views.eliminar_secretario, name='eliminar_secretario'),
    path('change_password/', CustomPasswordChangeView.as_view(), name="change_password")
]
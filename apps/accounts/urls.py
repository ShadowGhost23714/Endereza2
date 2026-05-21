from django.urls import path
from . import views
from .views import CustomLoginView, CustomPasswordChangeView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout

app_name = "accounts"

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('secretario/', views.secretario, name='secretario'),
    path('change_password/', CustomPasswordChangeView.as_view(), name="change_password")
]
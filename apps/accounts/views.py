from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages


# HOME
def home(request):
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {
        'usuarios': usuarios
    })


# LOGIN
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


# REGISTER
from .models import Profile

def register(request):
    if request.method == 'POST':
        username = request.POST['email']
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        dni = request.POST['dni']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('register')

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Crear perfil con DNI
        Profile.objects.create(user=user, dni=dni)

        return redirect('login')

    return render(request, 'accounts/register.html')
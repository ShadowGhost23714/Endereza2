from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Profile


# ───── HOME ─────
def home(request):
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {
        'usuarios': usuarios
    })


# ───── LOGIN ─────
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


# ───── REGISTER ─────
def register(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dni = request.POST.get('dni')

        # Validar usuario existente
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('accounts:register')

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Crear perfil
        Profile.objects.create(user=user, dni=dni)

        messages.success(request, 'Cuenta creada correctamente')
        return redirect('accounts:login')

    return render(request, 'accounts/register.html')


# ───── PROFILE ─────
@login_required
def profile(request):
    return render(request, "accounts/profile.html")
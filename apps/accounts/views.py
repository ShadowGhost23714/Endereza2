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
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return redirect('register')

        User.objects.create_user(username=username, password=password)
        return redirect('login')

    return render(request, 'accounts/register.html')
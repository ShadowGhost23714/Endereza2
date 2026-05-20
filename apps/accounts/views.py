from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import RegistroForm, LoginForm, CrearSecretarioForm
from django.contrib.auth.views import LoginView


User = get_user_model()


# ───── HOME ─────
def home(request):
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {
        'usuarios': usuarios
    })


# ───── LOGIN ─────
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)


# ───── REGISTER ─────
def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == 'POST':
        form = RegistroForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta creada correctamente')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Revisá los datos del formulario')

    else:
        form = RegistroForm()

    return render(request, 'accounts/register.html', {
        'form': form
    })


# ───── PROFILE ─────
@login_required
@never_cache
def profile(request):
    return render(request, "accounts/profile.html")

def secretario(request):
    if request.method == 'POST':
        form = CrearSecretarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Secretario creado correctamente")
            return redirect('accounts:login')
    else:
        form = CrearSecretarioForm()  # Sin argumentos — unbound

    return render(request, "accounts/secretario.html", {'form': form})
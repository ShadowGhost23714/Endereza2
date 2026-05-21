from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
<<<<<<< HEAD
from .forms import RegistroForm, LoginForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout

=======
from .forms import RegistroForm, LoginForm, CrearSecretarioForm
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy


>>>>>>> 670999417035d5001ef784a620dd7645a47d2a1f
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
<<<<<<< HEAD
=======

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, "Bienvenido 👋")
        return super().form_valid(form)
>>>>>>> 670999417035d5001ef784a620dd7645a47d2a1f


# ───── REGISTER ─────
def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == 'POST':
        form = RegistroForm(request.POST)

        if form.is_valid():
            form.save()
<<<<<<< HEAD
            messages.success(request, 'Cuenta creada correctamente')
=======
            messages.success(request, 'Cuenta creada correctamente 🎉')
>>>>>>> 670999417035d5001ef784a620dd7645a47d2a1f
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

<<<<<<< HEAD
=======

# ───── REGISTER SECRETARIO ─────
def secretario(request):
    if request.method == 'POST':
        form = CrearSecretarioForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente 🎉")
            return redirect('accounts:secretario')
    else:
        form = CrearSecretarioForm()

    return render(request, 'accounts/secretario.html', {
        'form': form
    })

# ───── PASSWORD CHANGE ─────
class CustomPasswordChangeView(PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Contraseña actualizada correctamente 🔒")
        return super().form_valid(form)
>>>>>>> 670999417035d5001ef784a620dd7645a47d2a1f

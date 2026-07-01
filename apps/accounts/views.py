from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import RegistroForm, LoginForm, CrearSecretarioForm, CustomPasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.http import JsonResponse


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

    def form_valid(self, form):
        messages.success(self.request, "Sesión iniciada correctamente 😉")
        return super().form_valid(form)
    def get_success_url(self):
        user = self.request.user
        if user.es_secretario:
            return reverse_lazy("turnos_view:turnos_del_dia")
        return reverse_lazy("core:home")
    
    #def get_success_url(self):
        #if self.request.user.is_superuser:
            #return reverse_lazy("core:home")
        #return reverse_lazy("core:home")
    

# ───── LOGOUT ─────
class CustomLogoutView(LogoutView):

    def post(self, request, *args, **kwargs):
        self.es_secretario = request.user.is_authenticated and request.user.es_secretario
        messages.success(request, "Sesión cerrada correctamente 👋")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("core:home")


# ───── REGISTER ─────
def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == 'POST':
        form = RegistroForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta creada correctamente 🎉')
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


# ───── REGISTER SECRETARIO ─────
@user_passes_test(lambda u: u.is_staff, login_url='accounts:login')
def secretario(request):
    if request.method == 'POST':
        form = CrearSecretarioForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente 🎉")
            return redirect('accounts:lista_secretarios')
        else:
            messages.error(request, 'Revisá los datos del formulario')
        
    else:
        form = CrearSecretarioForm()

    return render(request, 'accounts/secretario.html', {
        'form': form
    })

# ───── LISTA SECRETARIOS ─────
@user_passes_test(lambda u: u.is_staff, login_url='accounts:login')
def lista_secretarios(request):
    secretarios = User.objects.filter(tipo='secretario').order_by('last_name', 'first_name')
    return render(request, 'accounts/lista_secretarios.html', {
        'secretarios': secretarios
    })


# ───── ELIMINAR SECRETARIO ─────
@user_passes_test(lambda u: u.is_staff, login_url='accounts:login')
def eliminar_secretario(request, pk):
    if request.method == 'POST':
        secretario = User.objects.filter(pk=pk, tipo='secretario').first()
        if secretario:
            nombre = secretario.nombre_completo
            secretario.delete()
            messages.success(request, f"Secretario {nombre} eliminado correctamente 🗑️")
    return redirect('accounts:lista_secretarios')

# ───── PASSWORD CHANGE ─────
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Contraseña actualizada correctamente 🔒")
        return super().form_valid(form)


# ───── CANCEL ABONO ─────
@login_required
def cancelar_abono(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido."})
    user = request.user
    if not user.abono_activo:
        return JsonResponse({"ok": False, "error": "No tenés un abono activo."})
    # Marcamos como cancelado pero mantenemos la fecha de vencimiento
    user.tiene_abono_mensual = False
    user.save(update_fields=["tiene_abono_mensual"])
    return JsonResponse({"ok": True, "mensaje": f"Abono cancelado. Seguirá activo hasta el {user.abono_vencimiento.strftime('%d/%m/%Y')}."})

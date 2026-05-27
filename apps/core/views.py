from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.views import View

User = get_user_model()

User = get_user_model()

def home(request):

    usuarios = User.objects.all()
    return render(request, 'core/index.html', {'usuarios': usuarios})

def profile(request):
    return render(request, 'profile.html')

def turnos(request):
    return render(request, 'turnos.html')

def dueño(request):
    usuarios = User.objects.all()
    return render(request, 'core/dueño.html', {'usuarios': usuarios})

class HomeRouterView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return dueño(request)
        else:
            return home(request)
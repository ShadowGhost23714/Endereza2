from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.classes.models import Turno

User = get_user_model()

def home(request):

    usuarios = User.objects.all()
    turnos = Turno.objects.filter(fecha__gte=timezone.localdate()).order_by('fecha', 'hora_inicio')[:5]
    return render(request, 'core/index.html', {'usuarios': usuarios, 'turnos': turnos})

def profile(request):
    return render(request, 'profile.html')
from django.shortcuts import render
from django.contrib.auth.models import User

def home(request):
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {'usuarios': usuarios})

def profile(request):
    return render(request, 'profile.html')
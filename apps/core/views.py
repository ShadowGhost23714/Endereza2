from django.shortcuts import render
from django.contrib.auth import get_user_model
User = get_user_model()

def home(request):
    usuarios = User.objects.all()
    return render(request, 'core/index.html', {'usuarios': usuarios})

def profile(request):
    return render(request, 'profile.html')
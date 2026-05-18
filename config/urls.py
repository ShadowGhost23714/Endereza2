from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    # CORE
    path('', include('apps.core.urls')), 

    # ACCOUNTS (login, register, profile, etc)
    path('accounts/', include('apps.accounts.urls')),  

    # LOGOUT (opcional acá o dentro de accounts)
    path('logout/', LogoutView.as_view(), name='logout'),

    # project/urls.py
    path("turnos/", include("apps.classes.urls", namespace="turnos")),
    
    # payments/urls.py
    path("pagos/", include("apps.payments.urls")),
]
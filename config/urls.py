from django.contrib import admin
from django.urls import path, include
from apps.core.views import home
from apps.accounts.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # HOME
    path('', home, name='home'),

    # LOGIN
    path('login/', CustomLoginView.as_view(), name='login'),

    # REGISTER (esto conecta con accounts/urls.py)
    path('', include('apps.accounts.urls')),
]
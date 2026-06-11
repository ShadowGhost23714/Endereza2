from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings                          # ← agregar
from django.conf.urls.static import static               # ← agregar

urlpatterns = [
    path('admin/', admin.site.urls),

    # CORE
    path('', include('apps.core.urls')), 

    # ACCOUNTS (login, register, profile, etc)
    path('accounts/', include('apps.accounts.urls')),  
    
    path('professor/', include('apps.professor.urls')),  

    # LOGOUT (opcional acá o dentro de accounts)
    path('logout/', LogoutView.as_view(), name='logout'),

    # project/urls.py
    path("turnos/", include("apps.classes.urls", namespace="turnos")),
    
    # payments/urls.py
    path("pagos/", include("apps.payments.urls")),

    # turnos_view/urls.py
    path("agenda/", include("apps.turnos_view.urls")),

    # historial_pagos/urls.py
    path("historial-pagos/", include("apps.historial_pagos.urls", namespace="historial_pagos")),  # ← agregar

    # abonos/urls.py
    #path("abono/", include("apps.abonos.urls")),
]

if settings.DEBUG:                                        # ← agregar
    urlpatterns += static(                               # ← agregar
        settings.MEDIA_URL,                              # ← agregar
        document_root=settings.MEDIA_ROOT                # ← agregar
    )   
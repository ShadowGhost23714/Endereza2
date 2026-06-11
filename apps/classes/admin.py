from django.contrib import admin
from .models import Reserva, Turno, TurnoProfesional, Sala
from .models import Reserva, Sala, TurnoProfesional, Turno, CertificadoMedico

admin.site.register(Reserva)
admin.site.register(Turno)
admin.site.register(TurnoProfesional)
admin.site.register(Sala)
admin.site.register(CertificadoMedico)
from django.contrib import admin
from .models import Reserva, Turno, TurnoProfesional, Sala

admin.site.register(Reserva)
admin.site.register(Turno)
admin.site.register(TurnoProfesional)
admin.site.register(Sala)
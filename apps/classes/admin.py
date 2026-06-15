from django.contrib import admin
from .models import Reserva, Turno, TurnoProfesional, Sala
from .models import Reserva, Sala, TurnoProfesional, Turno, CertificadoMedico
from django import forms
from django.contrib import admin
from .models import CertificadoMedico

class CertificadoMedicoAdminForm(forms.ModelForm):
    imagen = forms.FileField(
        label="Imagen o PDF del certificado",
    )

    class Meta:
        model = CertificadoMedico
        fields = "__all__"

@admin.register(CertificadoMedico)
class CertificadoMedicoAdmin(admin.ModelAdmin):
    form = CertificadoMedicoAdminForm

admin.site.register(Reserva)
admin.site.register(Turno)
admin.site.register(TurnoProfesional)
admin.site.register(Sala)
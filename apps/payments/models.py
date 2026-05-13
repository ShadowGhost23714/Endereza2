from django.db import models
from django.utils import timezone

# Create your models here.
class PagoEfectivo (models.Model): 
    #Relaciono el pago con un turno unico
    turno= models.OneToOneField(Turno, on_delete=models.CASCADE, related_name='pago')

    #Monto pagado
    monto= models.DecimalField(max_digits=10, decimal_places=2)

    #Fecha y hora
    fecha_pago= models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Pago de ${self.monto} para el turno {self.turno.id} realizado el {self.fecha_pago}"

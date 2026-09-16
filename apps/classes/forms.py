from datetime import date, datetime, time
from django import forms
from .models import Sala, Turno, Profesor


class SelectWithCapacity(forms.Select):
    """Componente personalizado para incluir la capacidad de la sala en los <option>."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value and hasattr(value, 'value'):
            value = value.value
        
        # Si la opción tiene un ID de sala válido, busca su capacidad correspondiente
        if value:
            try:
                sala = Sala.objects.get(pk=value)
                option['attrs']['data-capacidad'] = sala.capacidad
            except Sala.DoesNotExist:
                pass
        return option
    
class SelectWithActivities(forms.Select):
    """Incluye la especialidad del profesor como data-attribute en cada <option>."""
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value and hasattr(value, 'value'):
            value = value.value
        
        if value:
            try:
                profesor = Profesor.objects.get(pk=value)
                # Guardamos el slug interno: "tren_inferior", "zona_media", "tren_superior"
                
                option['attrs']['data-especialidad'] = profesor.especialidad
            except Profesor.DoesNotExist:
                pass
        return option


class TurnoForm(forms.ModelForm):
    """Form for creating and editing a Turno."""

    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "min": date.today().isoformat(),
            },
        ),
        label="Fecha",
    )

    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "type": "time",
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "min": "08:00",
                "max": "20:00",
            },
        ),
        label="Hora de inicio",
    )

    

    # CORREGIDO: Usamos el componente personalizado 'SelectWithCapacity'
    sala = forms.ModelChoiceField(
        queryset=Sala.objects.all(),
        widget=SelectWithCapacity(
            attrs={
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "id": "id_sala",
            },
        ),
        label="Sala",
    )

    cupo = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "id": "id_cupo",
                "disabled": "disabled",
            },
        ),
        label="Cupo máximo",
    )

    actividad = forms.ChoiceField(
    # Usamos las choices de Profesor.Especialidad para que los valores coincidan
    choices=[("", "---------")] + list(Profesor.Especialidad.choices),
    widget=forms.Select(attrs={
        "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
                 "focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5",
        "id": "id_actividad"
    }),
    label="Actividad",
)

    # IGUAL A SALA: Usamos el nuevo widget personalizado
    profesor = forms.ModelChoiceField(
    queryset=Profesor.objects.all(),
        widget=SelectWithActivities(attrs={
            "class": (
                "bg-gray-900 border border-gray-300 text-gray-900 text-sm "
                "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                "block w-full p-2.5 transition-colors duration-200 "
            ),
            "id": "id_profesor",
            "disabled": "disabled",
        }),
        label="Profesor",
    )

    precio = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": (
                    "bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"
                ),
                "placeholder": "Ej: 15000",
            }
        ),
        label="Precio",
    )

    class Meta:
        model  = Turno
        fields = ["fecha", "hora_inicio", "sala", "cupo", "actividad", "profesor", "precio"]

    def __init__(self, *base_args, **kwargs):
        super().__init__(*base_args, **kwargs)
        # Customizamos la etiqueta para que muestre Nombre y DNI (asumiendo que el campo se llama 'dni')
        self.fields['profesor'].label_from_instance = lambda obj: f"{obj.dni} ({obj.nombre} {obj.apellido})"
        
        # Si prefieres que SOLO muestre el DNI, usa esta línea en su lugar:
        # self.fields['profesor'].label_from_instance = lambda obj: f"DNI: {obj.dni}"
    
    
    def clean(self):
        cleaned_data = super().clean()
        fecha        = cleaned_data.get("fecha")
        hora_inicio  = cleaned_data.get("hora_inicio")
        actividad    = cleaned_data.get("actividad")
        profesor     = cleaned_data.get("profesor")
        sala         = cleaned_data.get("sala")
        cupo         = cleaned_data.get("cupo")

        # Validación de profesor ocupado en el mismo turno
        if profesor and fecha and hora_inicio:
            qs_profesor = Turno.profesor_ocupado_en_turno(profesor, fecha, hora_inicio)
            if self.instance.pk:
                qs_profesor = qs_profesor.exclude(pk=self.instance.pk)
            if qs_profesor:
                self.add_error('profesor', "Este profesor ya tiene asignado un turno en esta fecha y hora.")

        # Validación de sala ocupada en el mismo turno
        if sala and fecha and hora_inicio:
            qs_sala = Turno.objects.filter(sala=sala, fecha=fecha, hora_inicio=hora_inicio)
            if self.instance.pk:
                qs_sala = qs_sala.exclude(pk=self.instance.pk)
            if qs_sala.exists():
                self.add_error('sala', "Esta sala ya está ocupada en la fecha y hora seleccionadas.")

        # Validación de cupo vs capacidad de la sala
        if sala and cupo:
            if cupo > sala.capacidad:
                self.add_error('cupo', f"El cupo no puede superar la capacidad de la sala ({sala.capacidad}).")

        # Validación de especialidad del profesor vs actividad
        if profesor and actividad:
            # Comparamos directamente contra el campo especialidad del profesor
            if profesor.especialidad != actividad:
                self.add_error('profesor', "El profesor seleccionado no dicta esta actividad.")

        # Validaciones adicionales para fecha y hora
        if fecha and hora_inicio and actividad:
            if fecha < date.today():
                raise forms.ValidationError("La fecha no puede ser en el pasado.")
            
            if hora_inicio.minute != 0 or hora_inicio.second != 0:
                raise forms.ValidationError("La hora de inicio debe ser en punto (ej: 08:00, 09:00).")

            if hora_inicio < time(8, 0) or hora_inicio > time(20, 0):
                raise forms.ValidationError("La hora de inicio debe estar entre las 08:00 y las 20:00 hs.")

            qs = Turno.objects.filter(fecha=fecha, hora_inicio=hora_inicio, actividad=actividad, sala=sala)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Ya existe una clase con esa actividad, sala, fecha y hora de inicio.")

        return cleaned_data

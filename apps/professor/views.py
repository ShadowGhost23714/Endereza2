# profesores/views.py

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import ProfesorForm
from .models import Profesor


class ProfesorCreateView(CreateView):
    """Renders and processes the form to create a new Profesor."""

    model         = Profesor
    form_class    = ProfesorForm
    template_name = "professor/profesor_form.html"
    success_url   = reverse_lazy("profesores:crear")   # stays on the same page after success

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"¡Profesor {self.object.nombre_completo} registrado correctamente!",
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Por favor corregí los errores indicados antes de continuar.",
        )
        return super().form_invalid(form)


class ProfesorListView(ListView):
    """Simple list of all professors (optional, handy for admin quick-look)."""

    model               = Profesor
    template_name       = "profesores/profesor_list.html"
    context_object_name = "profesores"
    paginate_by         = 20
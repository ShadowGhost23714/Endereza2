# profesores/views.py

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfesorForm
from .models import Profesor

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
    def handle_no_permission(self):
        return redirect('accounts:login')

class ProfesorCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Renders and processes the form to create a new Profesor."""

    model         = Profesor
    form_class    = ProfesorForm
    template_name = "professor/profesor_form.html"
    success_url   = reverse_lazy("profesores:lista")   # stays on the same page after success

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

class ProfesorDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model       = Profesor
    success_url = reverse_lazy("profesores:lista")

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(
            request,
            f"Profesor {self.object.nombre_completo} eliminado correctamente.",
        )
        return super().delete(request, *args, **kwargs)
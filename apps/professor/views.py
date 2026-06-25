# profesores/views.py


from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ProfesorForm
from .models import Profesor
import json
from django.http import JsonResponse
from django.views import View
from apps.classes.models import Turno, TurnoProfesional

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
    
class ProfesorDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):

    def post(self, request, pk):
        profesor = get_object_or_404(Profesor, pk=pk)

        # Leer reasignaciones enviadas desde el modal: {"turno_id": "nuevo_profesor_id", ...}
        try:
            reasignaciones = json.loads(request.POST.get("reasignaciones", "{}"))
        except (ValueError, TypeError):
            reasignaciones = {}

        # Clases actualmente asignadas a este profesor
        asignaciones = TurnoProfesional.objects.filter(id_profesor=profesor).select_related("id_turno")

        if asignaciones.exists():
            # Validar que todas tienen reasignación
            turno_ids_afectados = set(str(a.id_turno_id) for a in asignaciones)
            turno_ids_reasignados = set(reasignaciones.keys())

            if not turno_ids_afectados.issubset(turno_ids_reasignados):
                messages.error(request, "Debés asignar un nuevo profesor a todas las clases antes de eliminar.")
                return redirect("profesores:lista")

            # Aplicar reasignaciones
            for asignacion in asignaciones:
                nuevo_profesor_id = reasignaciones.get(str(asignacion.id_turno_id))
                if nuevo_profesor_id:
                    try:
                        nuevo_profesor = Profesor.objects.get(pk=nuevo_profesor_id)
                        turno = asignacion.id_turno
                        conflicto = Turno.profesor_ocupado_en_turno(nuevo_profesor, turno.fecha, turno.hora_inicio)
                        if conflicto:
                            messages.error(
                                request,
                                f"{nuevo_profesor.nombre_completo} ya tiene un turno asignado el "
                                f"{turno.fecha.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')}."
                            )
                        asignacion.id_profesor = nuevo_profesor
                        asignacion.save()
                    except Profesor.DoesNotExist:
                        messages.error(request, f"Profesor con id {nuevo_profesor_id} no encontrado.")
                        return redirect("profesores:lista")

        nombre = profesor.nombre_completo
        profesor.delete()
        messages.success(request, f"Profesor {nombre} eliminado correctamente.")
        return redirect("profesores:lista")


class ProfesorClasesAsignadasView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Devuelve JSON con las clases asignadas al profesor y la lista de otros profesores disponibles."""

    def get(self, request, pk):
        profesor = get_object_or_404(Profesor, pk=pk)
        asignaciones = (
            TurnoProfesional.objects
            .filter(id_profesor=profesor)
            .select_related("id_turno")
        )

        otros_profesores = Profesor.objects.exclude(pk=pk).filter(especialidad=profesor.especialidad)

        clases = []
        for a in asignaciones:
            turno = a.id_turno
            fecha = turno.fecha.strftime("%d/%m/%Y")
            hora  = turno.hora_inicio.strftime("%H:%M")

            disponibles = []
            for p in otros_profesores:
                ocupado = Turno.profesor_ocupado_en_turno(p, turno.fecha, turno.hora_inicio)
                if not ocupado:
                    disponibles.append({
                        "id":       p.pk,
                        "nombre":   p.nombre,
                        "apellido": p.apellido,
                    })

            clases.append({
                "turno_id":    turno.pk,
                "descripcion": f"{profesor.get_especialidad_display()} - {fecha} - {hora}",
                "disponibles": disponibles,
            })

        return JsonResponse({
            "clases":       clases,
            "especialidad": profesor.especialidad,
        })
        
class ProfesorCreateAjaxView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Crea un profesor via AJAX y devuelve JSON con el resultado."""

    def post(self, request):
        form = ProfesorForm(request.POST)
        if form.is_valid():
            profesor = form.save()
            return JsonResponse({
                "ok":      True,
                "id":      profesor.pk,
                "nombre":  profesor.nombre,
                "apellido": profesor.apellido,
                "especialidad": profesor.especialidad,
            })
        return JsonResponse({
            "ok":     False,
            "errors": form.errors,
        }, status=400)
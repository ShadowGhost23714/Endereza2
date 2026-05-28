from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ["last_name", "first_name"]
    list_display = ["email", "first_name", "last_name", "tipo", "tiene_abono_mensual", "abono_vencimiento"]
    list_filter  = ["tipo", "tiene_abono_mensual"]
    search_fields = ["email", "first_name", "last_name", "dni"]

    fieldsets = (
        ("Autenticación", {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "dni", "fecha_nacimiento")}),
        ("Rol", {"fields": ("tipo",)}),
        ("Abono", {"fields": ("tiene_abono_mensual", "abono_vencimiento")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Clases", {"fields": ("clases_a_favor",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "tipo", "password1", "password2"),
        }),
    )
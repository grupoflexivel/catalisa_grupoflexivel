from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'nome_completo')

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('nome_completo', 'must_change_password')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('nome_completo', 'must_change_password')}),
    )

admin.site.register(Usuario, UsuarioAdmin)

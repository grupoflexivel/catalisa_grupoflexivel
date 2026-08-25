from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


class UsuarioAdmin(UserAdmin):
    """
    Administração de usuários.

    A concessão do papel de gestor não exige nada especial aqui: o fieldset
    "Permissões", herdado do UserAdmin, já traz `groups` e `user_permissions`.
    Basta marcar o grupo **Gestores**. O que foi acrescentado abaixo é apenas o
    que faltava para *enxergar* quem tem o quê sem abrir usuário por usuário.
    """

    list_display = ('username', 'nome_completo', 'e_gestor', 'is_superuser', 'is_active')
    list_filter = ('groups', 'is_superuser', 'is_active', 'must_change_password')
    search_fields = ('username', 'nome_completo')
    ordering = ('nome_completo',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('nome_completo', 'must_change_password')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('nome_completo', 'must_change_password')}),
    )

    @admin.display(description="Gestor", boolean=True)
    def e_gestor(self, usuario):
        """
        Coluna de leitura: quem enxerga a aba de ideias.

        Pergunta pela permissão e não pelo grupo, porque ela também pode ter
        sido concedida direto no usuário — e o superusuário a tem por definição.
        """
        return usuario.has_perm("respostas.ver_todas_ideias")

    def get_queryset(self, request):
        # `has_perm` na coluna consulta grupos e permissões de cada linha.
        return super().get_queryset(request).prefetch_related(
            "groups__permissions", "user_permissions"
        )


admin.site.register(Usuario, UsuarioAdmin)

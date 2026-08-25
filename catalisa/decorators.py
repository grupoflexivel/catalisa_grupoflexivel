from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect

def acesso_administrador(view):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_superuser,
        login_url='login'
    )(view)


def acesso_gestor(view):
    """
    Libera a view para quem tem a permissão de ver todas as ideias.

    O superusuário passa sem estar no grupo: `has_perm` devolve True para
    superusuário ativo, então o administrador continua com acesso sem precisar
    de um `or user.is_superuser` aqui.
    """
    return user_passes_test(
        lambda user: user.is_authenticated and user.has_perm('respostas.ver_todas_ideias'),
        login_url='login'
    )(view)

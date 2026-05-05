from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect

def acesso_administrador(view):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_superuser,
        login_url='login'
    )(view)
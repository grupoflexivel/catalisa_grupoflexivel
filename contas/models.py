from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Modelo customizado de usuário com controle de expiração de senha.
    """
    nome_completo = models.CharField(max_length=85)
    username = models.CharField(max_length=25, unique=True, verbose_name="user")
    must_change_password = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.nome_completo
    
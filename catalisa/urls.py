"""
URL configuration for catalisa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from respostas.views import cadastrar_ideia, listar_ideias, ideia_cadastrada_com_sucesso
from contas.views import login_view, cadastro_view, ViewTrocaSenhaPrimeiroLogin, resetar_senha_usuario,home
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin-cat/', admin.site.urls),
    path("ideias/cadastro/", cadastrar_ideia, name="cadastrar_ideia"),
    path("login/", login_view, name="login"),
    path("cadastro/", cadastro_view, name="cadastro"),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('ideias/', listar_ideias, name='listar_ideias'),
    path('troca_senha/',ViewTrocaSenhaPrimeiroLogin.as_view(), name='troca_senha'),
    path('resetar_senha/', resetar_senha_usuario, name='resetar_senha'),
    path('cadastro_sucesso/',ideia_cadastrada_com_sucesso, name='cadastro_sucesso' ),
    path('', home, name='home')
]

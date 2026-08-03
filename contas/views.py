"""Módulo de views para controle de autenticação e fluxo de usuários.

Gerencia o ciclo de vida da sessão (login/logout), criação de contas por admins
e o fluxo de segurança para redefinição e troca obrigatória de senhas.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from .forms import (
    FormularioLogin,
    FormularioTrocaSenhaPrimeiroLogin,
    FormularioCriacaoUsuarioCustomizado,
    FormularioResetarSenha,
)
from catalisa.decorators import acesso_administrador
from django.contrib.auth import get_user_model
from django.contrib import messages
from typing import Union

User = get_user_model()


def requisicao_htmx(request: HttpRequest) -> bool:
    """Indica se a requisição foi disparada pelo HTMX."""
    return request.headers.get("HX-Request") == "true"


def redireciona_htmx(destino: str) -> HttpResponse:
    """
    Constrói a resposta que faz o HTMX navegar para outra página.

    O HTMX substitui apenas fragmentos da tela; para trocar de página após um
    envio bem-sucedido é necessário devolver o cabeçalho `HX-Redirect`.

    Args:
        destino (str): Nome da rota para onde o navegador deve ir.

    Returns:
        HttpResponse: Resposta vazia com a instrução de redirecionamento.
    """
    resposta = HttpResponse(status=204)
    resposta["HX-Redirect"] = reverse(destino)
    return resposta

def home(request: HttpRequest) -> HttpResponse:
    """
    Redireciona o fluxo principal do site para a página de login.
    
    Args:
        request (HttpRequest): Objeto contendo os metadados da requisição.
        
    Returns:
        HttpResponse: Resposta de redirecionamento para a rota nomeada 'login'.
    """
    return redirect('login')


@acesso_administrador
def cadastro_view(request: HttpRequest) -> HttpResponse:
    """
    Renderiza e processa o formulário de criação de novos usuários.

    Restrita a usuários com permissão de administrador através do decorator
    `@acesso_administrador`. Após o sucesso o administrador permanece na tela,
    com o formulário limpo, para cadastrar outro colaborador em sequência.

    Args:
        request: Objeto de requisição HTTP

    Returns:
        Resposta HTTP com o formulário ou redirecionamento.
    """
    if request.method == 'POST':
        user_form = FormularioCriacaoUsuarioCustomizado(request.POST)
        if user_form.is_valid():
            usuario = user_form.save()
            messages.success(
                request,
                f"Usuário {usuario.username} criado com sucesso. "
                "Ele deverá trocar a senha no primeiro acesso."
            )

            if requisicao_htmx(request):
                return redireciona_htmx('cadastro')

            return redirect('cadastro')

        if requisicao_htmx(request):
            return render(request, 'partials/_form_cadastro_usuario.html', {'user_form': user_form})

    else:
        user_form = FormularioCriacaoUsuarioCustomizado()

    return render(request,'cadastro.html', {'user_form':user_form})


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Gerencia a autenticação de usuários e o início da sessão.

    Se o usuário já estiver autenticado, redireciona para a página principal da aplicação.
    Em caso de falha nas credenciais, retorna uma mensagem de erro genérica.

    Args:
        request: Objeto de requisição HTTP.

    Returns:
        Renderização da página de login ou redirecionamento para a página principal da aplicação.
    """

    if request.user.is_authenticated:
        return redirect("cadastrar_ideia")

    if request.method == 'POST':
        login_form = FormularioLogin(request, data=request.POST)

        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)

            if requisicao_htmx(request):
                return redireciona_htmx("cadastrar_ideia")

            return redirect("cadastrar_ideia")

        else:
            #login_form.add_error(None, 'Usuário ou Senha Inválidos')

            if requisicao_htmx(request):
                return render(request, 'partials/_form_login.html', {'login_form': login_form})

    else:
        login_form = FormularioLogin()

    return render(request, 'login.html', {'login_form': login_form})

def logout_view(request: HttpRequest) -> HttpResponse:
    """Encerra a sessão atual do usuário e o redireciona para a tela de login.
    """
    logout(request)
    return redirect('login') 

class ViewTrocaSenhaPrimeiroLogin(LoginRequiredMixin,View):
    """
    Interface para o fluxo de troca de senha obrigatória no primeiro acesso.

    Exige que o usuário esteja logado (`LoginRequiredMixin`). 
    Após a troca bem-sucedida, atualiza o hash da sessão para evitar que o 
    usuário seja deslogado automaticamente e desativa a flag `must_change_password`.
    """
    template_name ="troca_senha_primeiro_acesso.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Exibe o formulário de troca de senha"""
        form = FormularioTrocaSenhaPrimeiroLogin(request.user)
        return render(request, self.template_name, {"form": form})
    
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Processa a nova senha e atualiza o estado de segurança do usuário.

        Args:
            request: Objeto de requisição contendo os dados da nova senha.

        Returns:
            Redirecionamento em caso de sucesso ou re-renderização com erros.
        """
        form = FormularioTrocaSenhaPrimeiroLogin(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            #Desativa a necessidade de troca de senha
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])

            #Mantém a sessão ativa após a troca de senha (evita logout por mudança de hash)
            update_session_auth_hash(request,user)

            messages.success(request, "Senha atualizada com sucesso. Bem-vindo ao Expandir!")

            if requisicao_htmx(request):
                return redireciona_htmx("cadastrar_ideia")

            return redirect("cadastrar_ideia")

        if requisicao_htmx(request):
            return render(request, "partials/_form_troca_senha.html", {"form": form})

        return render(request,self.template_name, {"form":form})
    
@acesso_administrador
def resetar_senha_usuario(request: HttpRequest) -> HttpResponse:
    """
    Permite que administradores forcem a redefinição de senha de terceiros.

    Essa view foi pensada para redefinir a senha quando o usuário esquece sua credencial.
    Utiliza o `FormularioResetarSenha` para validar o alvo e, após o sucesso,
    exibe uma mensagem de confirmação via `django.contrib.messages`.
    Args:
        request: Objeto de requisição HTTP.

    Returns:
        Renderização do formulário de reset ou redirecionamento após sucesso.
    """
    if request.method == "POST":
        form = FormularioResetarSenha(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Senha do usuário {user.username} foi redefinida com sucesso."
            )

            if requisicao_htmx(request):
                return redireciona_htmx("resetar_senha")

            return redirect("resetar_senha")

        if requisicao_htmx(request):
            return render(request, "partials/_form_resetar_senha.html", {"form": form})
    else:
        form = FormularioResetarSenha()

    return render(request, "resetar_senha.html", {"form": form})




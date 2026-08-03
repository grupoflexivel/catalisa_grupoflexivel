
import threading
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from catalisa.decorators import acesso_administrador
from .forms import IdeiaForm
from .models import Departamento, Ideia, UnidadeFabril
from django.core.paginator import Paginator
from respostas.integracao_notion import envia_ideia_para_notion_em_background

# Quantidade de ideias exibidas por página na listagem administrativa.
IDEIAS_POR_PAGINA = 9


def requisicao_htmx(request) -> bool:
    """
    Indica se a requisição foi disparada pelo HTMX.

    Permite que a mesma view devolva a página completa em uma navegação normal
    e apenas o fragmento correspondente quando o HTMX pede uma atualização
    parcial da tela.
    """
    return request.headers.get("HX-Request") == "true"


@login_required
def cadastrar_ideia(request):
    """
    Renderiza e processa o formulário de envio de ideias.

    Em requisições HTMX o formulário inválido volta como fragmento (trocando
    apenas o corpo do formulário, sem recarregar a página) e o envio válido
    responde com o cabeçalho `HX-Redirect`, que leva o navegador à tela de
    confirmação.
    """
    if request.method == "POST":
        form = IdeiaForm(request.POST,usuario_logado=request.user)
        if form.is_valid():
            ideia = form.save(commit=False)

            ideia.usuario_remetente_ideia = request.user #Capturo no backend a informação de quem enviou a ideia

            ideia.save()
            form.save_m2m()

            transaction.on_commit(
                lambda: threading.Thread(target=envia_ideia_para_notion_em_background,
                                         args=(ideia.id,),
                                         daemon=True,
                                    ).start()
                                )

            request.session['cadastro_sucesso'] = True

            if requisicao_htmx(request):
                resposta = HttpResponse(status=204)
                resposta["HX-Redirect"] = reverse("cadastro_sucesso")
                return resposta

            return redirect("cadastro_sucesso")

        if requisicao_htmx(request):
            return render(request, "partials/_form_ideia.html", {"form": form})
    else:
        form = IdeiaForm(usuario_logado=request.user)

    return render(request, "cadastrar_ideia.html", {"form": form})


@acesso_administrador
def listar_ideias(request):
    """
    Lista as ideias cadastradas com busca, filtros e paginação.

    A busca livre cobre título, autor, problema e descrição da ideia. Quando a
    requisição vem do HTMX apenas o fragmento da listagem é devolvido, o que
    permite filtrar e paginar sem recarregar a página inteira.
    """
    termo_busca = request.GET.get("q", "").strip()
    unidade_selecionada = request.GET.get("unidade", "").strip()
    departamento_selecionado = request.GET.get("departamento", "").strip()
    participacao_selecionada = request.GET.get("participacao", "").strip()

    ideias = (
        Ideia.objects
        .select_related("unidade_fabril", "departamento")
        .prefetch_related("beneficios", "integrantes_equipe")
        .order_by("-criado_em", "-id")
    )

    total_geral = Ideia.objects.count()

    if termo_busca:
        ideias = ideias.filter(
            Q(titulo__icontains=termo_busca)
            | Q(nome_autor__icontains=termo_busca)
            | Q(descricao_ideia__icontains=termo_busca)
            | Q(descricao_problema__icontains=termo_busca)
        )

    if unidade_selecionada.isdigit():
        ideias = ideias.filter(unidade_fabril_id=int(unidade_selecionada))

    if departamento_selecionado.isdigit():
        ideias = ideias.filter(departamento_id=int(departamento_selecionado))

    if participacao_selecionada in Ideia.TipoParticipacao.values:
        ideias = ideias.filter(forma_de_participacao=participacao_selecionada)

    total_filtrado = ideias.count()

    paginator = Paginator(ideias, IDEIAS_POR_PAGINA)
    pagina = paginator.get_page(request.GET.get("page"))

    contexto = {
        "ideias": pagina,
        "total_ideias": total_geral,
        "total_filtrado": total_filtrado,
        "termo_busca": termo_busca,
        "unidade_selecionada": unidade_selecionada,
        "departamento_selecionado": departamento_selecionado,
        "participacao_selecionada": participacao_selecionada,
        "filtros_ativos": bool(
            termo_busca
            or unidade_selecionada
            or departamento_selecionado
            or participacao_selecionada
        ),
        "unidades": UnidadeFabril.objects.order_by("nome"),
        "departamentos": Departamento.objects.order_by("nome"),
        "formas_participacao": Ideia.TipoParticipacao.choices,
    }

    if requisicao_htmx(request):
        return render(request, "partials/_ideias_resultado.html", contexto)

    return render(request, "listar_ideias.html", contexto)


@acesso_administrador
def detalhe_ideia(request, pk):
    """
    Devolve o conteúdo completo de uma ideia para exibição em modal.

    Sempre renderiza um fragmento: o HTMX injeta o resultado no container de
    modais declarado no layout base.
    """
    ideia = get_object_or_404(
        Ideia.objects
        .select_related("unidade_fabril", "departamento")
        .prefetch_related("beneficios", "integrantes_equipe"),
        pk=pk,
    )

    return render(request, "partials/_ideia_detalhe.html", {"ideia": ideia})


def ideia_cadastrada_com_sucesso(request):
    if not request.session.get('cadastro_sucesso'):
        raise Http404("Página não encontrada")

    del request.session['cadastro_sucesso']

    return render(request ,"cadastro_sucesso.html")

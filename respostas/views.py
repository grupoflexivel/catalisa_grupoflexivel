
import threading
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import content_disposition_header
from catalisa.decorators import acesso_gestor
from .forms import IdeiaForm
from .models import Departamento, DocumentoIdeia, FotoIdeia, Ideia, UnidadeFabril
from django.core.paginator import Paginator
from respostas.integracao_notion import envia_ideia_para_notion_em_background

# Quantidade de ideias exibidas por página na listagem administrativa.
IDEIAS_POR_PAGINA = 9

# Tipos aceitos pela rota de anexos. O mapa fechado existe para que o trecho
# da URL nunca vire uma consulta a um modelo arbitrário.
MODELOS_DE_ANEXO = {"foto": FotoIdeia, "documento": DocumentoIdeia}


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
        # request.FILES é obrigatório: sem ele o formulário enxerga os campos
        # de arquivo como vazios e o upload é silenciosamente descartado.
        form = IdeiaForm(request.POST, request.FILES, usuario_logado=request.user)
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


@acesso_gestor
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
        .prefetch_related("beneficios", "integrantes_equipe", "fotos", "documentos")
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


@acesso_gestor
def detalhe_ideia(request, pk):
    """
    Devolve o conteúdo completo de uma ideia para exibição em modal.

    Sempre renderiza um fragmento: o HTMX injeta o resultado no container de
    modais declarado no layout base.
    """
    ideia = get_object_or_404(
        Ideia.objects
        .select_related("unidade_fabril", "departamento")
        .prefetch_related("beneficios", "integrantes_equipe", "fotos", "documentos"),
        pk=pk,
    )

    return render(request, "partials/_ideia_detalhe.html", {"ideia": ideia})


def pode_ver_anexo(usuario, ideia) -> bool:
    """
    Quem enxerga a listagem enxerga os anexos dela; o autor vê os da própria ideia.

    A permissão é a mesma que abre a aba de ideias — administrador e gestor
    passam por aqui pelo mesmo caminho, sem checagem de papel duplicada.
    """
    if usuario.has_perm("respostas.ver_todas_ideias"):
        return True

    return bool(
        ideia.usuario_remetente_ideia
        and ideia.usuario_remetente_ideia == str(usuario)
    )


@login_required
def baixar_anexo_ideia(request, tipo, pk):
    """
    Entrega um anexo depois de conferir a permissão de quem pediu.

    Os arquivos não são servidos direto de /media/: quem tiver a URL leria o
    anexo de qualquer ideia sem passar pelo login. Em produção o nginx faz a
    entrega via X-Accel-Redirect — o Django decide, o nginx transfere, e o
    worker do Gunicorn não fica preso empurrando bytes.
    """
    modelo = MODELOS_DE_ANEXO.get(tipo)

    if modelo is None:
        raise Http404("Anexo inexistente")

    anexo = get_object_or_404(modelo.objects.select_related("ideia"), pk=pk)

    if not pode_ver_anexo(request.user, anexo.ideia):
        # 404 em vez de 403: não confirma para um curioso que o anexo existe.
        raise Http404("Anexo inexistente")

    # A foto abre na própria página; o documento vai como download.
    como_anexo = tipo == "documento"

    if settings.DEBUG:
        # No runserver não existe nginx para receber o X-Accel-Redirect.
        return FileResponse(
            anexo.arquivo.open("rb"), as_attachment=como_anexo, filename=anexo.nome_exibido
        )

    resposta = HttpResponse()
    # Content-Type vazio faz o nginx aplicar o tipo do arquivo pelo mime.types.
    del resposta["Content-Type"]
    resposta["X-Accel-Redirect"] = f"{settings.MEDIA_URL}{quote(anexo.arquivo.name)}"
    resposta["Content-Disposition"] = content_disposition_header(como_anexo, anexo.nome_exibido)
    resposta["X-Content-Type-Options"] = "nosniff"

    return resposta


def ideia_cadastrada_com_sucesso(request):
    if not request.session.get('cadastro_sucesso'):
        raise Http404("Página não encontrada")

    del request.session['cadastro_sucesso']

    return render(request ,"cadastro_sucesso.html")

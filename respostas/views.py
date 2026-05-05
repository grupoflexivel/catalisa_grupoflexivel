
import threading
from django.db import transaction
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from catalisa.decorators import acesso_administrador
from .forms import IdeiaForm
from .models import Ideia
from django.core.paginator import Paginator
from respostas.integracao_notion import envia_ideia_para_notion_em_background

@login_required
def cadastrar_ideia(request):
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
            return redirect("cadastro_sucesso")
    else:
        form = IdeiaForm(usuario_logado=request.user)

    return render(request, "cadastrar_ideia.html", {"form": form})

@acesso_administrador

def listar_ideias(request):
    ideias = Ideia.objects.all().order_by('id')
    total_ideias = ideias.count()

    paginator = Paginator(ideias, 10)
    page_number = request.GET.get('page')
    ideias = paginator.get_page(page_number)

    return render(request, 'listar_ideias.html', {'ideias': ideias, 'total_ideias': total_ideias})

def ideia_cadastrada_com_sucesso(request):
    if not request.session.get('cadastro_sucesso'):
        raise Http404("Página não encontrada")
    
    del request.session['cadastro_sucesso']
    
    return render(request ,"cadastro_sucesso.html")


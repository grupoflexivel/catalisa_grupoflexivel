# Frontend do programa Expandir

Documento de referência da camada visual da aplicação. Escrito para que qualquer
pessoa (ou sessão) consiga continuar o trabalho sem precisar reconstruir o
raciocínio por trás das decisões.

Última reformulação completa: **31/07/2026**.

---

## 1. Contexto

O programa de ideias do Grupo Flexível chamava-se **Catalisa** e passou a se
chamar **Expandir**. Toda a camada visual foi reconstruída nessa mudança:
antes eram templates HTML genéricos com um `base.css` escrito à mão; hoje é
Tailwind CSS + daisyUI + HTMX.

> **Atenção:** o pacote Python continua se chamando `catalisa/` (é o
> `DJANGO_SETTINGS_MODULE`, aparece no `entrypoint.sh`, no `docker-compose.yml`
> e no volume do Postgres). É nome interno, nunca exibido ao usuário. Renomear
> exige migração coordenada de deploy — não foi feito de propósito.
> Nenhum texto visível menciona "Catalisa".

---

## 2. Stack

| Biblioteca | Versão | Onde |
|---|---|---|
| Tailwind CSS (browser build) | 4.1.11 | `catalisa/static/vendor/tailwind-browser.js` |
| daisyUI | 5.0.x (baixado de `daisyui@5.0.50`; o banner do arquivo diz 5.0.49) | `catalisa/static/vendor/daisyui.css` |
| HTMX | 2.0.4 | `catalisa/static/vendor/htmx.min.js` |

**Por que vendorizado e não CDN:** a aplicação roda atrás de nginx em rede
corporativa. Arquivos locais eliminam dependência externa em runtime, e o
`collectstatic` do `entrypoint.sh` já os publica no volume estático.

Para atualizar alguma delas:

```bash
curl -sL -o catalisa/static/vendor/daisyui.css        https://cdn.jsdelivr.net/npm/daisyui@5/daisyui.css
curl -sL -o catalisa/static/vendor/tailwind-browser.js https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4
curl -sL -o catalisa/static/vendor/htmx.min.js         https://cdn.jsdelivr.net/npm/htmx.org@2/dist/htmx.min.js
```

O arquivo `daisyui-themes.css` também está baixado, mas **não é carregado** — os
temas prontos do daisyUI não são usados, apenas o tema próprio (seção 3).

O Tailwind aqui é o *browser build*: ele lê as classes do DOM e gera o CSS em
tempo de execução. Não existe passo de build, `package.json` ou Node no projeto.
Consequência prática: **classes montadas dinamicamente em string no Python ou no
JS não funcionam** — a classe precisa aparecer literalmente no HTML.

---

## 3. Identidade visual

Paleta extraída dos arquivos oficiais entregues pelo Marketing
(`catalisa/newfrontend/`, preservados como vieram):

| Cor | Hex | Papel |
|---|---|---|
| Teal profundo | `#003d3d` | `primary` — navbar ativa, títulos, botões |
| Gradiente laranja→vermelho | `#f27121 → #f06929 → #ec5440 → #e94057` | destaque de marca, faixa superior dos cards |
| Laranja | `#f27121` | `secondary` — badges, numeração de etapas |
| Vermelho | `#e94057` | `accent` — asterisco de campo obrigatório |
| Grafite | `#2e2d2c` | `neutral` |

O tema daisyUI se chama `expandir` e é declarado em
[catalisa/static/css/expandir.css](catalisa/static/css/expandir.css), ativado por
`<html data-theme="expandir">`. Para mexer em cores, mexa **só nas variáveis**
no topo desse arquivo — todos os componentes derivam delas.

### Assets de marca

`catalisa/static/brand/` (cópias com nomes sem espaço/acento, porque nomes
originais quebram URLs estáticas):

| Arquivo | Uso |
|---|---|
| `expandir-logo-color.svg` | navbar e drawer (fundo claro) |
| `expandir-logo-white.svg` | painel lateral escuro do login |
| `expandir-logo-black.svg` | rodapé |
| `expandir-icone.svg` / `.png` | favicon |
| `expandir-logo-semicolor.svg` | reserva, não usado ainda |

**`catalisa/static/logo.png` é o logo do Grupo Flexível e deve ser preservado** —
aparece no rodapé e no painel de login.

---

## 4. Mapa de arquivos

```
catalisa/
├── ui.py                        # classes CSS dos widgets + aplica_estilo_campos()
├── static/
│   ├── brand/                   # marca Expandir
│   ├── css/expandir.css         # tema daisyUI + estilos próprios (.exp-*)
│   ├── js/expandir.js           # comportamentos de interface (vanilla)
│   ├── vendor/                  # tailwind, daisyui, htmx
│   └── logo.png                 # Grupo Flexível — PRESERVAR
└── templates/
    ├── base.html                # layout autenticado: navbar + drawer + rodapé
    ├── base_auth.html           # layout split-screen: login e senhas
    ├── cadastrar_ideia.html     # formulário de ideia
    ├── listar_ideias.html       # lista admin com busca e filtros
    ├── cadastro.html            # criar usuário (admin)
    ├── resetar_senha.html       # resetar senha (admin)
    ├── troca_senha_primeiro_acesso.html
    ├── cadastro_sucesso.html
    └── partials/
        ├── _icons.html                  # sprite SVG (<use href="#i-nome"/>)
        ├── _messages.html               # toasts do django.contrib.messages
        ├── _campo.html                  # rótulo + widget + ajuda + erros
        ├── _campo_senha.html            # idem, com botão mostrar/ocultar
        ├── _form_ideia.html             # alvo HTMX do formulário de ideia
        ├── _form_login.html
        ├── _form_cadastro_usuario.html
        ├── _form_resetar_senha.html
        ├── _form_troca_senha.html
        ├── _ideias_resultado.html       # alvo HTMX da lista (cards + paginação)
        └── _ideia_detalhe.html          # conteúdo do modal
```

Removidos na reformulação: `base_minimal.html` e `static/css/base.css`.

### Qual layout estender

- **`base.html`** — telas de quem já está autenticado e navegando (formulário de
  ideia, lista, telas administrativas). Blocos: `title`, `page_badge`,
  `page_title`, `page_subtitle`, `page_actions`, `content`, `extra_head`, `scripts`.
- **`base_auth.html`** — telas de porta de entrada (login, troca de senha,
  confirmação de envio). Blocos: `title`, `aside_title`, `aside_text`,
  `aside_list`, `auth_badge`, `auth_title`, `auth_subtitle`, `content`, `auth_footer`.

---

## 5. Convenções de CSS

- **Utilitários do Tailwind e componentes do daisyUI resolvem 95% dos casos.**
  Só escreva CSS próprio quando o framework não cobrir.
- Todo estilo próprio usa o prefixo **`.exp-*`** e mora em `expandir.css`. O
  arquivo é carregado **fora de `@layer`**, então sempre vence o framework — por
  isso o prefixo é obrigatório, para nunca disputar com um utilitário.
- A ordem das camadas é fixada por um `<style>@layer theme, base, components,
  utilities;</style>` inline **antes** dos links de CSS no `<head>`. Sem isso, os
  utilitários do Tailwind perderiam para os componentes do daisyUI.

### ⚠️ Armadilha: `.hidden` não esconde elementos estilizados aqui

Regras fora de `@layer` vencem **qualquer** layer, independentemente da
especificidade. Como `expandir.css` fica fora de layer e o `.hidden` do Tailwind
mora em `@layer utilities`, todo seletor `.exp-*` que declare `display` torna o
`.hidden` inócuo naquele elemento — `classList.add("hidden")` roda, a classe
aparece no DOM, e nada acontece.

Foi o caso de `label.exp-choice` (`display: flex`), que deixava a busca do picker
e a exclusão do autor sem efeito. A solução é declarar o par no próprio arquivo:

```css
.exp-choices > div label.hidden,
label.exp-choice.hidden { display: none; }
```

Ao criar uma classe `.exp-*` com `display`, verifique se algum código a esconde
por classe e repita esse cuidado.

Classes próprias mais usadas:

| Classe | Efeito |
|---|---|
| `.exp-app-bg` | fundo da aplicação com halos de gradiente |
| `.exp-surface` | card translúcido com blur, borda e sombra |
| `.exp-topline` | faixa fina de gradiente no topo (requer `position: relative`) |
| `.exp-hero` | bloco teal escuro com brilho laranja (painéis de marca) |
| `.exp-lift` / `.exp-press` | microinterações de hover e clique |
| `.exp-fade-up` | animação de entrada |
| `.exp-label` | rótulo de campo |
| `.exp-field` / `.exp-field--invalid` | wrapper de campo e estado de erro |
| `.exp-choices` / `.exp-choice` | grupos de radio/checkbox em formato de cartão |
| `.exp-swap` | esmaece o bloco enquanto o HTMX o atualiza |
| `.exp-answer` | texto de resposta com quebra de linha preservada |

---

## 6. Formulários

### Renderizando um campo

```django
{% include "partials/_campo.html" with campo=form.titulo %}
{% include "partials/_campo.html" with campo=form.valor ajuda="Texto de apoio" %}
{% include "partials/_campo_senha.html" with campo=form.password sem_ajuda=True %}
```

`sem_ajuda=True` suprime o `help_text` padrão do Django (útil nos campos de senha,
cujo texto padrão é uma lista enorme de validadores).

### Estilizando widgets

As classes ficam em [catalisa/ui.py](catalisa/ui.py) (`INPUT_CLASS`,
`SELECT_CLASS`, `TEXTAREA_CLASS`) e são aplicadas de duas formas:

- **Formulários próprios** — direto em `Meta.widgets` (ver `respostas/forms.py`).
- **Formulários herdados do Django** (`AuthenticationForm`, `UserCreationForm`,
  `SetPasswordForm`) — pela função `aplica_estilo_campos(form, placeholders={...})`
  no `__init__`, que complementa as classes existentes.

### ⚠️ Armadilha: RadioSelect e CheckboxSelectMultiple

O template `multiple_input.html` do Django repete o atributo `class` do widget
**no container `<div>` e em cada `<input>`**. Colocar `checkbox checkbox-primary`
ali desenha uma caixa de checkbox em volta do grupo inteiro.

Por isso esses widgets são declarados **sem `attrs`** e a estilização vem da
estrutura, via wrapper no template:

```django
<div class="exp-field exp-choices exp-choices--cols">
  <label class="exp-label">{{ form.beneficios.label }}</label>
  {{ form.beneficios }}
  {{ form.beneficios.errors }}
</div>
```

O CSS mira `.exp-choices > div` (o container) e `.exp-choices > div label`
(cada opção). O estado marcado usa `label:has(input:checked)`.

### ⚠️ Armadilha: `col-span-2` em grid de uma coluna

`grid gap-5` sem `grid-cols-*` tem uma coluna. Um filho com `sm:col-span-2`
**cria uma segunda coluna implícita** e quebra o layout dos irmãos. Ou declare
`sm:grid-cols-2` no container, ou não use `col-span`.

---

## 7. Padrões HTMX

Três padrões cobrem a aplicação inteira. Ao criar tela nova, reaproveite um deles.

### 7.1 Formulário que se substitui

O `<form>` inteiro é o alvo. Erro → volta o fragmento; sucesso → `HX-Redirect`.

```django
<form method="post" action="{% url 'x' %}"
      hx-post="{% url 'x' %}" hx-target="this" hx-swap="outerHTML"
      hx-disabled-elt="find button[type=submit]">
  {% csrf_token %}
  ...
  <button type="submit" class="exp-action btn btn-primary">
    <span class="loading loading-spinner loading-sm htmx-indicator"></span>
    <span class="exp-action-label">Enviar</span>
  </button>
</form>
```

Na view:

```python
if form.is_valid():
    ...
    if requisicao_htmx(request):
        return redireciona_htmx("destino")   # HTTP 204 + HX-Redirect
    return redirect("destino")

if requisicao_htmx(request):
    return render(request, "partials/_form_x.html", {"form": form})   # HTTP 200
```

O fragmento precisa voltar com **status 200** — o HTMX ignora respostas 4xx por
padrão. E `action`/`method` continuam preenchidos para funcionar sem JavaScript.

### 7.2 Lista com busca, filtros e paginação

O formulário de filtros dispara `hx-get` mirando o container de resultados:

```django
hx-get="{% url 'listar_ideias' %}"
hx-target="#resultado-ideias" hx-swap="innerHTML"
hx-indicator="#resultado-ideias, #spinner-busca"
hx-push-url="true" hx-sync="this:replace"
hx-trigger="change delay:150ms, keyup changed delay:350ms from:#busca-ideias, search from:#busca-ideias, submit"
```

`hx-push-url` mantém o botão *voltar* do navegador funcionando; `hx-sync`
cancela requisições em voo quando o usuário continua digitando. Os botões de
paginação, dentro do próprio fragmento, usam `{% querystring page=N %}` (tag
nativa do Django 5.1+) para preservar os filtros ativos.

Na view, `requisicao_htmx(request)` decide entre a página inteira e o fragmento.

### 7.3 Modal sob demanda

```django
<button hx-get="{% url 'detalhe_ideia' ideia.id %}"
        hx-target="#exp-modal" hx-swap="innerHTML" hx-indicator="this">
```

A view devolve um `<dialog class="modal">`. O `expandir.js` detecta o swap em
`#exp-modal`, chama `showModal()` e limpa o container no `close`. O `#exp-modal`
existe nos dois layouts base.

### CSRF

O `<body>` de ambos os layouts carrega
`hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`, que o HTMX herda para toda
requisição da página. Ainda assim, **mantenha `{% csrf_token %}` dentro dos
formulários** — é o que os faz funcionar sem JavaScript.

---

## 8. Comportamentos do `expandir.js`

Tudo por delegação de evento, então continua valendo em conteúdo trocado pelo
HTMX. As rotinas são idempotentes e reexecutadas em `htmx:afterSwap`.

| Recurso | Como usar |
|---|---|
| **Campo condicional** | `data-show-when="nome_do_campo" data-show-values="A\|B"` no bloco (com `class="hidden"`). Adicione `data-show-when-label` para comparar pelo texto do rótulo em vez do value — é o caso do benefício "Outros", cujo value é um ID. |
| **Seletor de pessoas** | `data-exp-picker data-max="3"` no wrapper; dentro, `[data-picker-search]`, `[data-picker-chips]`, `[data-picker-empty]` e opções `label.exp-choice[data-picker-option]`. Trava a seleção no máximo e gera chips removíveis. Para **seleção única** (campo do autor), use radios e omita `data-max`, `[data-picker-chips]` e `[data-picker-count]` — sobra só a busca. |
| **Excluir uma opção do picker** | `data-picker-exclude-field="<name de outro campo>"` no wrapper. A opção cujo input tem o mesmo `value` do que está escolhido naquele campo some da lista e é desmarcada. Serve para radios ou lista suspensa; é o que tira o autor da lista de integrantes. |
| **Mostrar/ocultar senha** | `data-toggle-password="id_do_input"` no botão (já embutido em `_campo_senha.html`). |
| **Toast programático** | `showToast(texto, "success"\|"error"\|"warning")`, ou dispare o evento `expandir:toast` no `body` a partir de um header `HX-Trigger`. |
| **Barra de progresso** | automática em toda requisição HTMX (`#exp-progress`). |
| **Foco no erro** | após um envio recusado, rola até o primeiro `.exp-field--invalid` e foca o controle. |

Ícones: `<svg class="size-5"><use href="#i-nome"/></svg>`. O catálogo está em
`partials/_icons.html` (traço 1.75, grade 24×24, estilo Lucide).

---

## 9. Backend tocado nesta reformulação

Nada de modelo ou migração mudou. As alterações foram de apresentação e de
suporte ao HTMX:

- **`catalisa/ui.py`** (novo) — tokens de classe dos widgets + `aplica_estilo_campos`.
- **`catalisa/urls.py`** — rota `ideias/<int:pk>/` (`detalhe_ideia`, modal) e
  identidade do admin do Django (`site_header`).
- **`respostas/views.py`** — helper `requisicao_htmx`; busca (`q`) e filtros
  (`unidade`, `departamento`, `participacao`) na listagem; `IDEIAS_POR_PAGINA = 9`;
  `select_related`/`prefetch_related` na consulta; view `detalhe_ideia`.
- **`respostas/forms.py`** — widgets com classes daisyUI e placeholders;
  `integrantes_equipe` passou de `SelectMultiple` (Select2) para
  `CheckboxSelectMultiple`; `empty_label` das listas suspensas.
- **`contas/views.py`** — helpers `requisicao_htmx` / `redireciona_htmx`; respostas
  parciais nas quatro views de conta.
- **`contas/forms.py`** — `FormularioLogin` (substitui o `AuthenticationForm` cru,
  só para estilo/autocomplete) e `__init__` de estilo nos demais formulários.

### Decisões com efeito funcional

1. **jQuery e Select2 foram removidos.** O seletor de integrantes agora é o
   componente próprio de checkboxes com busca.
2. **Bug corrigido em `respostas/forms.py`**: `integrantes_equipe > 3` comparava
   QuerySet com int e levantava `TypeError` — toda ideia em grupo quebrava no
   envio. Hoje é `.count() > MAXIMO_INTEGRANTES_EQUIPE`.
3. **Após criar um usuário**, o administrador permanece em `/cadastro/` com toast
   de confirmação, em vez de ser mandado para `/login/`.
4. **A listagem ordena por `-criado_em`** (era `id` crescente).
5. **`nome_autor` virou uma lista de colaboradores.** Era um campo de texto
   livre; agora é um `ModelChoiceField` (`RadioSelect`) sobre o mesmo queryset de
   `integrantes_equipe`, declarado no `IdeiaForm` fora do `Meta` e renderizado no
   mesmo formato do seletor de integrantes — busca por digitação e lista rolável
   de cartões. O modelo não mudou: `clean_nome_autor` devolve o `nome_completo`
   do usuário escolhido, e é essa string que continua sendo gravada no
   `CharField`.
6. **O autor não pode ser integrante da própria equipe**, verificado por ID: a
   opção correspondente ao autor selecionado some da lista (`expandir.js`) e o
   `clean()` recusa o envio se ela vier mesmo assim.
7. **A regra deixou de olhar o usuário logado.** Quem cadastra nem sempre é o
   autor — alguém pode registrar a ideia no lugar de um colega. O usuário logado
   apenas pré-seleciona o autor e pode ser integrante da equipe normalmente;
   quem manda é o autor escolhido.

---

## 10. Como rodar e testar

### Local (mais rápido)

Exige o Postgres de `.env` ativo em `localhost:5432`.

```bash
venv/Scripts/python.exe manage.py runserver 8000
```

→ http://127.0.0.1:8000/login/ — use **Ctrl+F5** na primeira carga após mudanças
de CSS.

### Docker

```bash
docker compose up --build     # http://localhost:5003
```

⚠️ O `.env` versionado usa `DATABASE_URL=...@localhost:5432/...`, que **não
resolve de dentro do container `web`** — para esse caminho o host precisa ser
`db`. O `collectstatic` roda sozinho no `entrypoint.sh`.

### Roteiro de verificação manual

1. Login com senha errada → erro sem recarregar a página.
2. Formulário de ideia: **Grupo** revela os integrantes; benefício **"Outros"**
   revela o campo de texto; envio incompleto mostra erros inline e rola até o
   primeiro.
3. Listagem: digitar na busca atualiza sozinho após ~350 ms; filtros e paginação
   não recarregam mas mudam a URL (botão *voltar* funciona); "Ver ideia completa"
   abre o modal.
4. Janela abaixo de 1024 px → menu vira hambúrguer com drawer.

### Conferência visual automatizada

Não há navegador nas ferramentas padrão, mas dá para tirar screenshot com o Edge
headless (foi assim que as telas foram validadas):

```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  --headless=new --no-sandbox --disable-gpu --hide-scrollbars `
  --window-size=1440,1200 --virtual-time-budget=9000 `
  --screenshot="saida.png" --user-data-dir="$env:TEMP\edgeprofile" `
  "http://127.0.0.1:8000/login/"
```

Para telas que exigem sessão, renderize o HTML com o `django.test.Client`, grave
em `catalisa/static/_preview/` (as URLs `/static/...` continuam resolvendo) e
aponte o navegador para lá — **apagando a pasta depois**.

---

## 11. Pendências e próximos passos sugeridos

Nada abaixo é bloqueante; são as continuações naturais.

- [ ] **Painel de indicadores** para o administrador (ideias por unidade, por
      área, por mês). O `dataviz` seria o guia de estilo dos gráficos.
- [ ] **Exportar a listagem** para CSV/Excel a partir dos filtros aplicados.
- [ ] **Editar `status_ideia`** pela interface — o campo existe no modelo e já é
      exibido no modal, mas hoje só muda pelo admin do Django ou pelo Notion.
- [ ] **Tela de "minhas ideias"** para o colaborador acompanhar o que enviou
      (hoje ele só cadastra e não revê).
- [ ] **Tema escuro** — a estrutura de variáveis já suporta; falta declarar um
      bloco `[data-theme="expandir-dark"]` e um seletor de tema.
- [ ] **Testes automatizados de verdade** — a validação atual foi um script de
      fumaça descartável. Vale portar para `respostas/tests.py` e `contas/tests.py`.
- [ ] Avaliar a **renomeação do pacote `catalisa/` para `expandir/`** em uma
      janela de manutenção, com ajuste de `entrypoint.sh`, `docker-compose.yml`,
      `manage.py`, `wsgi/asgi` e imports.

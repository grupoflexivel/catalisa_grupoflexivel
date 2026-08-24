from pathlib import Path

from django import forms
from .models import Ideia, Beneficio
from .models import DocumentoIdeia, FotoIdeia
from .validators import (
    EXTENSOES_DOCUMENTO,
    EXTENSOES_IMAGEM,
    MAXIMO_DOCUMENTOS,
    MAXIMO_FOTOS,
    valida_extensao_documento,
    valida_extensao_imagem,
    valida_tamanho_anexo,
)
from contas.models import Usuario
from catalisa.ui import FILE_CLASS, INPUT_CLASS, SELECT_CLASS, TEXTAREA_CLASS

# Limite de integrantes adicionais em ideias enviadas por equipe.
MAXIMO_INTEGRANTES_EQUIPE = 3


class MultipleFileInput(forms.ClearableFileInput):
    """
    Input de arquivo que aceita seleção múltipla.

    `allow_multiple_selected` é o que faz o Django ler `files.getlist(name)` em
    vez de `files.get(name)`; sem isso apenas o último arquivo escolhido
    chegaria à view.
    """

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    Campo que devolve uma lista de arquivos, validando cada um isoladamente.

    Receita da documentação do Django ("Uploading multiple files"): não existe
    campo pronto para isso porque `FileField.clean` foi escrito para um arquivo
    só — aqui ele é aplicado em laço.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpa_um = super().clean

        if isinstance(data, (list, tuple)):
            return [limpa_um(arquivo, initial) for arquivo in data]

        return [limpa_um(data, initial)]


class IdeiaForm(forms.ModelForm):
    # O autor é escolhido na mesma lista de colaboradores oferecida em
    # `integrantes_equipe`. Assim a regra "o autor não é integrante da própria
    # equipe" se resolve comparando IDs, e não o texto do nome. O modelo continua
    # guardando apenas o nome (`nome_autor` é um CharField): o usuário
    # selecionado vira texto em `clean_nome_autor`.
    # O widget é declarado sem `attrs`: o template multiple_input.html do Django
    # repetiria a classe no container e em cada <input>. A estilização vem da
    # estrutura (.exp-choice), como no campo de integrantes.
    nome_autor = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        label="Autor da ideia",
        empty_label=None,
        widget=forms.RadioSelect(),
    )

    # Anexos. Ficam fora do Meta porque não são campos do modelo Ideia: cada
    # arquivo vira uma linha em FotoIdeia/DocumentoIdeia depois que a ideia
    # ganha um id. `accept` só pré-filtra a janela do sistema operacional —
    # quem recusa o arquivo é o servidor, em clean_fotos/clean_documentos.
    fotos = MultipleFileField(
        required=False,
        label="Fotos (opcional)",
        help_text=f"Até {MAXIMO_FOTOS} imagens JPG, PNG ou WEBP de 10 MB cada. "
                  "Segure Ctrl para escolher várias de uma vez.",
        widget=MultipleFileInput(attrs={
            "class": FILE_CLASS,
            "accept": ",".join(f".{extensao}" for extensao in EXTENSOES_IMAGEM),
        }),
    )

    documentos = MultipleFileField(
        required=False,
        label="Documentos (opcional)",
        help_text=f"Até {MAXIMO_DOCUMENTOS} arquivos PDF, Word, Excel, PowerPoint, "
                  "CSV ou TXT de 10 MB cada.",
        widget=MultipleFileInput(attrs={
            "class": FILE_CLASS,
            "accept": ",".join(f".{extensao}" for extensao in EXTENSOES_DOCUMENTO),
        }),
    )

    class Meta:
        model = Ideia
        fields = [
            "nome_autor",
            "unidade_fabril",
            "departamento",
            "forma_de_participacao",
            "integrantes_equipe",
            "titulo",
            "descricao_problema",
            "impacto_problema",
            "causa_problema",
            "descricao_ideia",
            "como_a_ideia_resolve_problema",
            "participacao_implementacao",
            "beneficios",
            "outros_beneficios",
            "ganhos_esperados",
            "necessidades_ideia",
            "valor_estimado_ideia",
            "prazo_estimado_ideia",
        ]
        widgets = {
            "unidade_fabril": forms.Select(attrs={"class": SELECT_CLASS}),
            "departamento": forms.Select(attrs={"class": SELECT_CLASS}),
            "forma_de_participacao": forms.RadioSelect(),
            "integrantes_equipe": forms.CheckboxSelectMultiple(),
            "titulo": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Resuma a ideia em uma frase"}),
            "descricao_problema": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "Descreva o que acontece hoje e onde acontece."}),
            "impacto_problema": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "Retrabalho, custo, tempo parado, risco, qualidade..."}),
            "causa_problema": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "O que faz o problema se repetir?"}),
            "descricao_ideia": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 5, "placeholder": "Explique como a solução funcionaria na prática."}),
            "como_a_ideia_resolve_problema": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "Qual parte do problema deixa de existir?"}),
            "participacao_implementacao": forms.RadioSelect(),
            "beneficios": forms.CheckboxSelectMultiple(),
            "outros_beneficios": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Descreva os outros benefícios"}),
            "ganhos_esperados": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "Ganhos em números sempre que possível."}),
            "necessidades_ideia": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 4, "placeholder": "Pessoas, equipamentos, sistemas, apoio de outra área..."}),
            "valor_estimado_ideia": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Ex.: aproximadamente R$ 4.000"}),
            "prazo_estimado_ideia": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Ex.: 2 meses"}),
        }
        labels = {
            "unidade_fabril": "Unidade/Planta",
            "departamento": "Área/Departamento",
            "forma_de_participacao": "Forma de participação",
            "integrantes_equipe": "Integrantes da equipe",
            "titulo": "Título da Ideia",
            "descricao_problema": "1. Qual problema ou oportunidade você identificou?",
            "impacto_problema": "2. Qual o impacto desse problema?",
            "causa_problema": "3. Por que esse problema acontece hoje?",
            "descricao_ideia": "4. Qual é a sua ideia? Descreva de forma clara como ela funciona.",
            "como_a_ideia_resolve_problema": "5. Como ela resolve ou ameniza o problema?",
            "participacao_implementacao": "6. Se a sua ideia for escolhida você gostaria de participar da implementação?",
            "beneficios": "7. Quais os principais benefícios esperados?",
            "outros_beneficios": "Outros benefícios",
            "ganhos_esperados": "8. Quais são os ganhos esperados?",
            "necessidades_ideia": "9. Do que precisamos para tirar sua ideia do papel?",
            "valor_estimado_ideia": "10. Qual valor estimado para implementação da ideia?",
            "prazo_estimado_ideia": "11. Qual prazo estimado para implementação da ideia?",
        }

    def __init__(self, *args, **kwargs):
        self.usuario_logado = kwargs.pop("usuario_logado", None)
        super().__init__(*args, **kwargs)

        # Usuário escolhido como autor, preservado por clean_nome_autor para a
        # comparação por ID feita em clean().
        self.autor = None

        colaboradores = Usuario.objects.filter(
            is_staff=False,
            is_superuser=False,
            is_active=True,
        ).order_by("nome_completo")

        self.fields["nome_autor"].queryset = colaboradores
        self.fields["integrantes_equipe"].queryset = colaboradores

        # Quem está cadastrando costuma ser o próprio autor, mas pode trocar:
        # o registro pode estar sendo feito no lugar de outro colaborador.
        if (
            self.usuario_logado
            and self.usuario_logado.is_authenticated
            and colaboradores.filter(pk=self.usuario_logado.pk).exists()
        ):
            self.fields["nome_autor"].initial = self.usuario_logado.pk

        # Textos de apoio nas listas suspensas, no lugar do "---------" padrão
        self.fields["unidade_fabril"].empty_label = "Selecione a unidade"
        self.fields["departamento"].empty_label = "Selecione a área"

    def _valida_anexos(self, campo, maximo, validadores, plural):
        """
        Aplica o limite de quantidade e os validadores a cada arquivo da lista.

        Os validadores precisam ser chamados à mão: eles moram nos modelos
        FotoIdeia/DocumentoIdeia, que só serão criados depois — o formulário é
        a última barreira antes de o arquivo ir para o disco.
        """
        arquivos = self.cleaned_data.get(campo) or []

        if len(arquivos) > maximo:
            raise forms.ValidationError(
                f"Envie no máximo {maximo} {plural}. Você selecionou {len(arquivos)}."
            )

        erros = []

        for arquivo in arquivos:
            for validador in validadores:
                try:
                    validador(arquivo)
                except forms.ValidationError as erro:
                    # O nome entra na mensagem para o usuário saber qual dos
                    # arquivos precisa trocar.
                    erros.extend(f"{arquivo.name}: {mensagem}" for mensagem in erro.messages)

        if erros:
            raise forms.ValidationError(erros)

        return arquivos

    def clean_fotos(self):
        return self._valida_anexos(
            "fotos", MAXIMO_FOTOS, [valida_extensao_imagem, valida_tamanho_anexo], "fotos"
        )

    def clean_documentos(self):
        return self._valida_anexos(
            "documentos", MAXIMO_DOCUMENTOS, [valida_extensao_documento, valida_tamanho_anexo],
            "documentos",
        )

    def _cria_anexos(self, ideia):
        """
        Cria as linhas de anexo. Só roda depois que a ideia tem `pk`.

        O nome original é guardado aqui porque `upload_to` troca o nome do
        arquivo por um UUID no momento em que ele vai para o disco.
        """
        FotoIdeia.objects.bulk_create([
            FotoIdeia(ideia=ideia, arquivo=arquivo, nome_original=Path(arquivo.name).name[:255])
            for arquivo in self.cleaned_data.get("fotos", [])
        ])

        DocumentoIdeia.objects.bulk_create([
            DocumentoIdeia(ideia=ideia, arquivo=arquivo, nome_original=Path(arquivo.name).name[:255])
            for arquivo in self.cleaned_data.get("documentos", [])
        ])

    def save(self, commit=True):
        """
        Salva a ideia e, junto, os anexos.

        Com `commit=False` os anexos entram na fila do `save_m2m()` — mesmo
        motivo dos ManyToMany: eles precisam de uma ideia já gravada para
        apontar. Assim a view continua com o fluxo que já tinha (`save(commit=False)`
        → completa o objeto → `save()` → `save_m2m()`) sem precisar saber que
        existem anexos.
        """
        ideia = super().save(commit=commit)

        if commit:
            self._cria_anexos(ideia)
        else:
            salva_m2m_original = self.save_m2m

            def salva_m2m():
                salva_m2m_original()
                self._cria_anexos(ideia)

            self.save_m2m = salva_m2m

        return ideia

    def clean_nome_autor(self):
        """
        Guarda o usuário selecionado e devolve o nome, que é o que o modelo grava.
        """
        autor = self.cleaned_data.get("nome_autor")
        self.autor = autor

        return autor.nome_completo if autor else ""

    def clean(self):
        cleaned_data = super().clean()
        forma_de_participacao = cleaned_data.get("forma_de_participacao")
        integrantes_equipe = cleaned_data.get("integrantes_equipe")
        beneficios = cleaned_data.get("beneficios")
        outros_beneficios = cleaned_data.get("outros_beneficios")

        # O autor já faz parte da equipe e não se repete entre os integrantes.
        # A interface remove essa opção da lista; aqui a regra vale também sem
        # JavaScript.
        if self.autor and integrantes_equipe is not None:
            if integrantes_equipe.filter(pk=self.autor.pk).exists():
                self.add_error(
                    "integrantes_equipe",
                    "O autor da ideia já faz parte da equipe e não deve ser "
                    "selecionado como integrante."
                )

        if (
            forma_de_participacao == Ideia.TipoParticipacao.GRUPO
            and not integrantes_equipe
        ):
            self.add_error(
                "integrantes_equipe",
                "Informe os integrantes da equipe quando a participação for em grupo."
            )

        if (
            forma_de_participacao == Ideia.TipoParticipacao.GRUPO
            and integrantes_equipe is not None
            and integrantes_equipe.count() > MAXIMO_INTEGRANTES_EQUIPE
        ):
            self.add_error(
                "integrantes_equipe",
                f"Além do autor, cada equipe pode ter no máximo {MAXIMO_INTEGRANTES_EQUIPE} integrantes."
            )

        outros_selecionado = False
        if beneficios:
            outros_selecionado = beneficios.filter(nome__iexact="Outros").exists()

        if outros_selecionado and not outros_beneficios:
            self.add_error(
                "outros_beneficios",
                "Descreva os outros benefícios selecionados."
            )

        return cleaned_data
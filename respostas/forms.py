from django import forms
from .models import Ideia, Beneficio
from contas.models import Usuario
from catalisa.ui import INPUT_CLASS, SELECT_CLASS, TEXTAREA_CLASS

# Limite de integrantes adicionais em ideias enviadas por equipe.
MAXIMO_INTEGRANTES_EQUIPE = 3


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
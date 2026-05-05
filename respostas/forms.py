from django import forms
from .models import Ideia, Beneficio
from contas.models import Usuario


class IdeiaForm(forms.ModelForm):
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
            "nome_autor": forms.TextInput(attrs={"class": "form-control"}),
            "unidade_fabril": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "forma_de_participacao": forms.RadioSelect(attrs={"class": "choice-input"}),
            "integrantes_equipe": forms.SelectMultiple(attrs={"class": "select2-integrantes", "data-placeholder": "Digite ou selecione os integrantes"}),
            "titulo": forms.TextInput(attrs={"class": "form-control"}),
            "descricao_problema": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "impacto_problema": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "causa_problema": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "descricao_ideia": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "como_a_ideia_resolve_problema": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "participacao_implementacao": forms.RadioSelect(attrs={"class": "choice-input"}),
            "beneficios": forms.CheckboxSelectMultiple(attrs={"class": "choice-input"}),
            "outros_beneficios": forms.TextInput(attrs={"class": "form-control"}),
            "ganhos_esperados": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "necessidades_ideia": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "valor_estimado_ideia": forms.TextInput(attrs={"class": "form-control"}),
            "prazo_estimado_ideia": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "nome_autor": "Nome completo",
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

        queryset = Usuario.objects.filter(
            is_staff=False,
            is_superuser=False,
        )

        if self.usuario_logado and self.usuario_logado.is_authenticated:
            queryset = queryset.exclude(id=self.usuario_logado.id)

        self.fields["integrantes_equipe"].queryset = queryset

    def clean_integrantes_equipe(self):
        integrantes = self.cleaned_data.get("integrantes_equipe")

        if self.usuario_logado and integrantes.filter(id=self.usuario_logado.id).exists():
            raise forms.ValidationError(
                "Você não pode incluir seu próprio usuário como integrante da equipe."
            )

        return integrantes

    def clean(self):
        cleaned_data = super().clean()
        forma_de_participacao = cleaned_data.get("forma_de_participacao")
        integrantes_equipe = cleaned_data.get("integrantes_equipe")
        beneficios = cleaned_data.get("beneficios")
        outros_beneficios = cleaned_data.get("outros_beneficios")

        if (
            forma_de_participacao == Ideia.TipoParticipacao.GRUPO
            and not integrantes_equipe
        ):
            self.add_error(
                "integrantes_equipe",
                "Informe os integrantes da equipe quando a participação for em grupo."
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
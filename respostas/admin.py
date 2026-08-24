from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Beneficio,
    Departamento,
    DocumentoIdeia,
    FotoIdeia,
    Ideia,
    UnidadeFabril,
)
from .validators import MAXIMO_DOCUMENTOS, MAXIMO_FOTOS

admin.site.register(UnidadeFabril)
admin.site.register(Departamento)
admin.site.register(Beneficio)


class AnexoInline(admin.TabularInline):
    """
    Base dos inlines de anexo, com prévia do que já está salvo.

    `max_num` é o que impede o administrador de passar do limite pela tela —
    o mesmo teto que o formulário público aplica.
    """

    extra = 1
    readonly_fields = ("previa", "nome_original", "criado_em")
    tipo = ""

    @admin.display(description="Prévia")
    def previa(self, anexo):
        if not anexo.pk:
            return "—"

        url = reverse("baixar_anexo_ideia", args=[self.tipo, anexo.pk])

        if self.tipo == "foto":
            return format_html(
                '<a href="{0}" target="_blank" rel="noopener">'
                '<img src="{0}" style="max-height:120px;border-radius:8px;border:1px solid #ddd">'
                "</a>",
                url,
            )

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a> ({})',
            url, anexo.nome_exibido, anexo.tamanho_legivel,
        )


class FotoIdeiaInline(AnexoInline):
    model = FotoIdeia
    max_num = MAXIMO_FOTOS
    tipo = "foto"


class DocumentoIdeiaInline(AnexoInline):
    model = DocumentoIdeia
    max_num = MAXIMO_DOCUMENTOS
    tipo = "documento"


@admin.register(Ideia)
class IdeiaAdmin(admin.ModelAdmin):
    """
    Administração das ideias, com os anexos visíveis já na listagem.
    """

    inlines = (FotoIdeiaInline, DocumentoIdeiaInline)
    list_display = ("titulo", "nome_autor", "unidade_fabril", "status_ideia", "criado_em", "anexos_resumo")
    list_filter = ("unidade_fabril", "departamento", "status_ideia", "forma_de_participacao")
    search_fields = ("titulo", "nome_autor", "descricao_problema", "descricao_ideia")
    date_hierarchy = "criado_em"
    filter_horizontal = ("beneficios", "integrantes_equipe")
    readonly_fields = ("criado_em", "atualizado_em")

    fieldsets = (
        ("Identificação", {
            "fields": ("titulo", "nome_autor", "unidade_fabril", "departamento",
                       "forma_de_participacao", "integrantes_equipe"),
        }),
        ("O problema", {
            "fields": ("descricao_problema", "impacto_problema", "causa_problema"),
        }),
        ("A solução", {
            "fields": ("descricao_ideia", "como_a_ideia_resolve_problema", "participacao_implementacao"),
        }),
        ("Impactos", {
            "fields": ("beneficios", "outros_beneficios", "ganhos_esperados"),
        }),
        ("Viabilidade", {
            "fields": ("necessidades_ideia", "valor_estimado_ideia", "prazo_estimado_ideia"),
        }),
        ("Rastreabilidade", {
            "fields": ("usuario_remetente_ideia", "status_ideia", "criado_em", "atualizado_em"),
        }),
    )

    @admin.display(description="Anexos")
    def anexos_resumo(self, ideia):
        """Marcadores compactos na listagem, sem abrir cada registro."""
        marcadores = []
        # len(...all()) e não .count(): assim o prefetch do get_queryset é
        # aproveitado em vez de disparar um COUNT por linha.
        total_fotos = len(ideia.fotos.all())
        total_documentos = len(ideia.documentos.all())

        if total_fotos:
            marcadores.append(f"🖼️ {total_fotos}")
        if total_documentos:
            marcadores.append(f"📄 {total_documentos}")

        return " · ".join(marcadores) or "—"

    def get_queryset(self, request):
        # Sem isto, `anexos_resumo` faria duas consultas por linha da listagem.
        return super().get_queryset(request).prefetch_related("fotos", "documentos")

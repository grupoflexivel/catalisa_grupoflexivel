import uuid
from pathlib import Path

from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from contas.models import Usuario
from django.utils.translation import gettext_lazy as _

from .validators import (
    valida_extensao_documento,
    valida_extensao_imagem,
    valida_tamanho_anexo,
)


def _caminho_anexo(subpasta, filename):
    """
    Monta o caminho de destino de um anexo dentro de MEDIA_ROOT.

    O nome enviado pelo navegador é descartado e substituído por um UUID por
    três motivos: ele é controlado pelo usuário (evita `../` e nomes que o
    sistema de arquivos recusa), pode conter informação indesejada, e nomes
    aleatórios impedem que alguém descubra o arquivo de outra pessoa chutando
    a URL. Só a extensão é aproveitada — e ela já passou pelos validadores.

    Ex.: anexos/ideias/2026/08/fotos/9f2c1ab4e8f0473e9c1b0d1a2e3f4a5b.jpg
    """
    extensao = Path(filename).suffix.lower()
    hoje = timezone.localdate()

    return f"anexos/ideias/{hoje:%Y/%m}/{subpasta}/{uuid.uuid4().hex}{extensao}"


def caminho_foto_ideia(instance, filename):
    """Destino da foto. Função nomeada porque a migração precisa importá-la."""
    return _caminho_anexo("fotos", filename)


def caminho_documento_ideia(instance, filename):
    """Destino do documento. Função nomeada, pelo mesmo motivo acima."""
    return _caminho_anexo("documentos", filename)

class UnidadeFabril(models.Model):

    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Unidade Fabril"
        verbose_name_plural = "Unidades Fabris"

    def __str__(self):
        return self.nome

class Departamento(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=85)

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=85)


class Beneficio(models.Model):
    id = models.AutoField(primary_key=True)
    nome = nome = models.CharField(max_length=150)

    class Meta:
        verbose_name = "Benefício"
        verbose_name_plural = "Benefícios"

    def __str__(self):
        return self.nome
    
class Ideia(models.Model):

    class TipoParticipacao(models.TextChoices):
        INDIVIDUAL = 'IND', _('Individual')
        GRUPO = 'GRP', _('Grupo')

    class EscolhaSimples(models.TextChoices):
        SIM = "Sim", _('Sim')
        NAO = "Não", _('Não')

    class Meta:
        verbose_name = "Ideia"
        verbose_name_plural = "Ideias cadastradas"

    id = models.AutoField(primary_key=True)
    nome_autor = models.CharField(max_length=125)
    unidade_fabril = models.ForeignKey(UnidadeFabril, on_delete=models.PROTECT,related_name="unidade_fabril_ideia")
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT,related_name="departamento_ideia")
    forma_de_participacao = models.CharField(max_length=3, choices=TipoParticipacao.choices, default=TipoParticipacao.INDIVIDUAL, verbose_name="forma_de_participacao")
    integrantes_equipe = models.ManyToManyField(Usuario, blank=True, verbose_name="Integrantes da equipe") #Só é util se escolherem "grupo" no "forma_de_participacao"
    titulo = models.CharField(max_length=200)

    #O Problema(A "Dor")
    descricao_problema = models.CharField(max_length=1000)
    impacto_problema = models.CharField(max_length=1000)
    causa_problema = models.CharField(max_length=1000)

    #A Solução("Oportunidade")
    descricao_ideia = models.CharField(max_length=1400)
    como_a_ideia_resolve_problema = models.CharField(max_length=500)
    participacao_implementacao = models.CharField(max_length=3, choices=EscolhaSimples.choices, verbose_name="participacao_implementacao")

    #Impactos e Resultados esperados
    beneficios = models.ManyToManyField(Beneficio)
    outros_beneficios = models.CharField(max_length=255, blank=True, null=True) #Não é obrigado a marcar o "Outros"
    ganhos_esperados = models.CharField(max_length=550)

    #Viabilidade e recursos
    necessidades_ideia = models.CharField(max_length=500)
    valor_estimado_ideia = models.CharField(max_length=300) #Usei CharField para caso o usuário escreva coisas como "Uns 4mil reais"
    prazo_estimado_ideia = models.CharField(max_length=300)

    # Os anexos ficam em FotoIdeia e DocumentoIdeia (mais de um por ideia).

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    #Rastreabilidade e status
    usuario_remetente_ideia = models.CharField(max_length=100,null=True,blank=True)
    status_ideia = models.CharField(max_length=100,null=True,blank=True,default="Nova")

    def __str__(self):
        return self.titulo

    @property
    def tem_anexos(self):
        """
        Verdadeiro se a ideia tem qualquer anexo.

        Avalia `.all()` em vez de chamar `.exists()`: o template itera as
        mesmas coleções logo depois, e assim o prefetch da view é aproveitado
        em vez de somar dois SELECTs extras.
        """
        return bool(self.fotos.all() or self.documentos.all())


class AnexoIdeia(models.Model):
    """
    Base comum de foto e documento.

    Abstrata em vez de concreta com um campo `tipo`: as duas pontas têm
    validadores, limites e widgets diferentes, e a foto precisa ser um
    `ImageField` de verdade — é ele que manda o Pillow abrir o arquivo e recusa
    um .jpg que não é imagem, checagem que um `FileField` genérico não faz.
    """

    # O nome em disco vira UUID; este é o nome que a pessoa reconhece.
    nome_original = models.CharField(max_length=255, blank=True, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.nome_exibido

    @property
    def nome_exibido(self):
        return self.nome_original or Path(self.arquivo.name).name

    @property
    def tamanho_legivel(self):
        return filesizeformat(self.arquivo.size)


class FotoIdeia(AnexoIdeia):
    ideia = models.ForeignKey(Ideia, on_delete=models.CASCADE, related_name="fotos")
    arquivo = models.ImageField(
        upload_to=caminho_foto_ideia,
        max_length=255,
        validators=[valida_extensao_imagem, valida_tamanho_anexo],
    )

    class Meta(AnexoIdeia.Meta):
        verbose_name = "Foto da ideia"
        verbose_name_plural = "Fotos da ideia"


class DocumentoIdeia(AnexoIdeia):
    ideia = models.ForeignKey(Ideia, on_delete=models.CASCADE, related_name="documentos")
    arquivo = models.FileField(
        upload_to=caminho_documento_ideia,
        max_length=255,
        validators=[valida_extensao_documento, valida_tamanho_anexo],
    )

    class Meta(AnexoIdeia.Meta):
        verbose_name = "Documento da ideia"
        verbose_name_plural = "Documentos da ideia"


@receiver(post_delete, sender=FotoIdeia)
@receiver(post_delete, sender=DocumentoIdeia)
def remove_arquivo_do_disco(sender, instance, **kwargs):
    """
    Apaga o arquivo quando o registro é apagado.

    O Django não faz isso sozinho desde a 1.3 — sem este gancho, excluir uma
    ideia limparia o banco e deixaria os arquivos ocupando o volume para
    sempre. O `on_commit` garante que nada seja apagado se a transação que
    fez o DELETE acabar revertida.
    """
    arquivo = instance.arquivo

    if arquivo:
        transaction.on_commit(lambda: arquivo.delete(save=False))

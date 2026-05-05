from django.db import models
from contas.models import Usuario
from django.utils.translation import gettext_lazy as _

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

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    #Rastreabilidade e status
    usuario_remetente_ideia = models.CharField(max_length=100,null=True,blank=True)
    status_ideia = models.CharField(max_length=100,null=True,blank=True,default="Nova")

    def __str__(self):
        return self.titulo
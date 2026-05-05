import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catalisa.settings')

django.setup()

from respostas.models import Ideia

Ideia.objects.all()
ideia = Ideia.objects.last()

for campo in ideia._meta.fields:
    print(campo.name, "=", getattr(ideia, campo.name))


#Para ver como dicionário, que dará o output igual abaixo:

#from django.forms.models import model_to_dict

#model_to_dict(ideia)

# id <class 'int'> 2
# nome_autor <class 'str'> Usuario Teste
# unidade_fabril <class 'int'> 1
# departamento <class 'int'> 1
# forma_de_participacao <class 'str'> IND
# integrantes_equipe <class 'str'> 
# titulo <class 'str'> Validação de um Formulário
# descricao_problema <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# impacto_problema <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# causa_problema <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# descricao_ideia <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# como_a_ideia_resolve_problema <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# participacao_implementacao <class 'str'> Não
# outros_beneficios <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# ganhos_esperados <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# necessidades_ideia <class 'str'> As vezes as pessoas escrevem qualquer coisa nesses formulários só para testar mesmo
# valor_estimado_ideia <class 'str'> Olha, vai uma boa grana, uns R$8745,27
# prazo_estimado_ideia <class 'str'> 5 horas em marte
# beneficios <class 'list'> [<Beneficio: Melhoria na segurança ou bem-estar do colaborador.>, <Beneficio: Melhoria na experiência do cliente final>, <Beneficio: Ganho de tempo>, <Beneficio: Outros (quais)>]
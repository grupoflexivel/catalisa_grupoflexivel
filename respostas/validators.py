"""
Regras de validação dos anexos enviados junto com uma ideia.

Ficam em módulo próprio, como objetos de nível de módulo, porque o Django
serializa os validadores dentro do arquivo de migração: uma `lambda` ou uma
função aninhada não seriam importáveis e quebrariam o `makemigrations`.
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import filesizeformat

# O nginx da frente corta o corpo da requisição em 20 MB (client_max_body_size).
# O limite da aplicação fica abaixo disso para que o usuário receba um erro de
# formulário legível em vez do 413 cru do servidor web.
TAMANHO_MAXIMO_ANEXO = 10 * 1024 * 1024

# Quantos arquivos de cada tipo uma ideia aceita. O limite é aplicado no
# formulário (onde vira erro legível) e nos inlines do admin.
MAXIMO_FOTOS = 5
MAXIMO_DOCUMENTOS = 3

EXTENSOES_IMAGEM = ["jpg", "jpeg", "png", "webp"]
EXTENSOES_DOCUMENTO = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv", "txt"]

valida_extensao_imagem = FileExtensionValidator(
    allowed_extensions=EXTENSOES_IMAGEM,
    message="Envie uma imagem nos formatos JPG, PNG ou WEBP.",
)

valida_extensao_documento = FileExtensionValidator(
    allowed_extensions=EXTENSOES_DOCUMENTO,
    message="Formato não aceito. Envie PDF, Word, Excel, PowerPoint, CSV ou TXT.",
)


def valida_tamanho_anexo(arquivo):
    """
    Recusa arquivos acima de `TAMANHO_MAXIMO_ANEXO`.

    O tamanho é lido do objeto de upload, não de um cabeçalho enviado pelo
    navegador, então não dá para burlar declarando um `Content-Length` menor.
    """
    if arquivo.size > TAMANHO_MAXIMO_ANEXO:
        raise ValidationError(
            "O arquivo tem %(tamanho)s e o limite é %(limite)s."
            % {
                "tamanho": filesizeformat(arquivo.size),
                "limite": filesizeformat(TAMANHO_MAXIMO_ANEXO),
            }
        )

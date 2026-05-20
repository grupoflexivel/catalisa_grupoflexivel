import os
import requests
from dotenv import load_dotenv
import logging
from respostas.models import Ideia

load_dotenv()

logger = logging.getLogger(__name__)

def envia_ideia_para_notion_em_background(ideia_id):
    try:
        ideia = Ideia.objects.get(id=ideia_id)
        json_envio_ideia(ideia)

        logger.info(f"Ideia enviada para o Notion com sucesso. ID={ideia_id}")

    except Ideia.DoesNotExist:
        logger.warning(f"Ideia não encontrada para envio ao Notion. ID={ideia_id}")

    except Exception:
        logger.exception(f"Erro ao enviar ideia para o Notion. ID={ideia_id}")

def json_envio_ideia(ideia):
    token = os.getenv("NOTION_TOKEN")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    notion_version = os.getenv("NOTION_VERSION", "2022-06-28")

    if not token:
        raise ValueError("NOTION_TOKEN não encontrado no .env")

    if not notion_database_id:
        raise ValueError("NOTION_DATABASE_ID não encontrado no .env")

    url = "https://api.notion.com/v1/pages"
    headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Notion-Version": notion_version, 
    }
    data = {
        "parent": {"database_id": notion_database_id},
        "properties": {

            "Autor": {
                "rich_text": [
                    {
                        "text": {"content": ideia.nome_autor or ""}
                    }
                ]
            },
            "Departamento": {
                "select": {"name": str(ideia.departamento)}
            },
            "Titulo": {
                "title": [
                    {
                        "text": {"content": ideia.titulo or ""}
                    }
                ]
            },
            "Problema - Descrição": {
                "rich_text": [
                    {
                        "text": {"content": ideia.descricao_problema or ""}
                    }
                ]
            },
            "Problema - Impacto": {
                "rich_text": [
                    {
                        "text": {"content": ideia.impacto_problema or ""}
                    }
                ]
            },
            "Problema - Causa": {
                "rich_text": [
                    {
                    "text": {"content": ideia.causa_problema or ""}
                    }
                ]
            },
            "Solução - Ideia": {
                "rich_text": [
                    {
                        "text": {"content": ideia.descricao_ideia or ""}
                    }
                ]
            },
            "Solução - Como resolve": {
                "rich_text": [
                    {
                        "text": {"content": ideia.como_a_ideia_resolve_problema or ""}
                    }
                ]
            },
            "Unidade Fabril": {
                "select":{
                    "name": str(ideia.unidade_fabril)
                }
            },
            "Solução - Participação": {
                "select": {
                    "name": ideia.participacao_implementacao
                    }
            },
            "Forma de Participação":{
                "select": {
                    "name": ideia.get_forma_de_participacao_display()
                    }
            },
            "Integrantes da Equipe":{
                "multi_select": [
                    {"name": integrante.nome_completo} for integrante in ideia.integrantes_equipe.all() or ""
                    
                ]
            },
            "Benefícios":{
                "multi_select": [
                    {"name": beneficio.nome} for beneficio in ideia.beneficios.all() or ""
                ]
            },

            "Outros Benefícios":{
                "rich_text":[
                    {
                        "text":{"content":ideia.outros_beneficios or ""}
                    }
                ]
            },
            
            "Ganhos Esperados":{
                "rich_text":[
                    {
                        "text":{"content":ideia.ganhos_esperados or ""}
                    }
                ]
            },
            
            "Ideia - Necessidade":{
                "rich_text":[
                    {
                        "text":{"content":ideia.necessidades_ideia or ""}
                    }
                ]
            },
            
            "Ideia - Valor Estimado":{
                "rich_text":[
                    {
                        "text":{"content":ideia.valor_estimado_ideia or ""}
                    }
                ]
            },

            "Ideia - Prazo Estimado":{
                "rich_text":[
                    {
                        "text":{"content":ideia.prazo_estimado_ideia or ""}
                    }
                ]
            },

            "Status da Ideia": {
                "select": {
                    "name": "Novas"
                    }
            },


        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Sucesso! Página criada no Notion.")
    else:
        error_details = response.json()
        print(f"Erro {response.status_code}: {error_details.get('message', 'Erro desconhecido')}")
        print(f"Detalhes: {error_details}")
        

if __name__ == "__main__":
    envia_ideia_para_notion_em_background()
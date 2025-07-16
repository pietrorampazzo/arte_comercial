import os
import requests
import json

# URL base da API de Licitações do Portal de Compras
BASE_API_URL = "https://compras.dados.gov.br/licitacoes/v1"


def obter_metadados_licitacao(uasg, id_licitacao):
    """
    Busca os metadados de uma licitação na API do Portal de Compras.

    Args:
        uasg (str): O código da Unidade Administrativa de Serviços Gerais (UASG).
        id_licitacao (str): O ID da licitação.

    Returns:
        dict: Um dicionário com os metadados da licitação, ou None em caso de erro.
    """
    numero_licitacao = id_licitacao[8:13]
    ano_licitacao = id_licitacao[13:]
    url = f"{BASE_API_URL}/pregoes?uasg={uasg}&numero_pregao={numero_licitacao}&ano_pregao={ano_licitacao}"
    print(f"Buscando metadados em: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança uma exceção para códigos de erro HTTP
        data = response.json()
        if data and "_embedded" in data and "licitacoes" in data["_embedded"]:
            return data["_embedded"]["licitacoes"][0]
        else:
            print("Não foram encontrados metadados para esta licitação.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar metadados da licitação: {e}")
        return None

def baixar_documentos_licitacao(uasg, id_licitacao):
    """
    Baixa os documentos de uma licitação a partir do UASG e do ID da licitação.

    Args:
        uasg (str): O código da Unidade Administrativa de Serviços Gerais (UASG).
        id_licitacao (str): O ID da licitação.
    """
    print(f"Iniciando download dos documentos para a licitação {id_licitacao} da UASG {uasg}...")

    # Etapa 1: Obter metadados da licitação
    metadados = obter_metadados_licitacao(uasg, id_licitacao)
    if not metadados:
        return

    # Etapa 2: Criar diretório para salvar os arquivos
    nome_licitacao = f"licitacao_{uasg}_{id_licitacao}"
    if not os.path.exists(nome_licitacao):
        os.makedirs(nome_licitacao)

    # Etapa 3: Baixar edital e anexos
    baixar_edital(metadados, nome_licitacao)
    baixar_anexos(metadados, nome_licitacao)

    print("Download dos documentos concluído com sucesso!")


def baixar_edital(metadados, diretorio):
    """
    Baixa o edital da licitação.

    Args:
        metadados (dict): Os metadados da licitação.
        diretorio (str): O diretório onde o edital será salvo.
    """
    if "link_edital" in metadados:
        url_edital = metadados["link_edital"]
        print(f"Baixando edital de: {url_edital}")
        try:
            response = requests.get(url_edital)
            response.raise_for_status()
            # O nome do arquivo é extraído da URL
            nome_arquivo = os.path.join(diretorio, "edital.pdf")
            with open(nome_arquivo, "wb") as f:
                f.write(response.content)
            print(f"Edital salvo em: {nome_arquivo}")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o edital: {e}")

def baixar_anexos(metadados, diretorio):
    """
    Baixa os anexos da licitação.

    Args:
        metadados (dict): Os metadados da licitação.
        diretorio (str): O diretório onde os anexos serão salvos.
    """
    if "anexos" in metadados:
        for anexo in metadados["anexos"]:
            if "link" in anexo:
                url_anexo = anexo["link"]
                print(f"Baixando anexo de: {url_anexo}")
                try:
                    response = requests.get(url_anexo)
                    response.raise_for_status()
                    # O nome do arquivo é extraído da URL
                    nome_arquivo = os.path.join(diretorio, url_anexo.split("/")[-1])
                    with open(nome_arquivo, "wb") as f:
                        f.write(response.content)
                    print(f"Anexo salvo em: {nome_arquivo}")
                except requests.exceptions.RequestException as e:
                    print(f"Erro ao baixar o anexo: {e}")


if __name__ == "__main__":
    # Exemplo de uso com os dados da UTFPR
    # ATENÇÃO: As licitações da UTFPR não foram encontradas na API de dados abertos do Compras.gov.br.
    # O código abaixo funcionará para licitações que estejam disponíveis na API.
    UASG_EXEMPLO = "153177"
    # O ID da licitação é composto pelo UASG + modalidade + numero
    ID_LICITACAO_EXEMPLO = "15317705900122023"
    baixar_documentos_licitacao(UASG_EXEMPLO, ID_LICITACAO_EXEMPLO)

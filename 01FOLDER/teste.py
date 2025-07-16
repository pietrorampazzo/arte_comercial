import requests
from datetime import datetime
import time

def formatar_data(data_iso):
    try:
        dt_obj = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
        return dt_obj.strftime("%d/%m/%Y às %H:%M Hs")
    except:
        return "Data não disponível"

def obter_dados_api(url, params=None):
    try:
        headers = {"Accept": "application/json"}
        resposta = requests.get(url, headers=headers, params=params, timeout=15)
        resposta.raise_for_status()
        
        # Respeita limites de taxa
        if "X-RateLimit-Remaining" in resposta.headers and int(resposta.headers["X-RateLimit-Remaining"]) < 5:
            time.sleep(1)
            
        return resposta.json()
    except requests.exceptions.HTTPError as e:
        print(f"Erro na requisição: {e.response.status_code}")
        if e.response.text:
            print(f"Detalhes: {e.response.text[:200]}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Falha de conexão: {str(e)}")
        return None

def buscar_licitacao_por_uasg_numero(uasg, numero_pregao, ano):
    """Busca direta usando parâmetros UASG e número do pregão"""
    url = "https://compras.dados.gov.br/pregoes/v1/pregoes.json"
    params = {
        "uasg": uasg,
        "numero": numero_pregao,
        "ano": ano
    }
    
    return obter_dados_api(url, params)

def obter_itens_licitacao(id_licitacao):
    """Obtém todos os itens da licitação com paginação"""
    url = f"https://compras.dados.gov.br/pregoes/v1/itens_pregao/{id_licitacao}.json"
    resposta = obter_dados_api(url)
    
    if not resposta:
        return None
    
    itens = resposta.get("_embedded", {}).get("item", [])
    
    # Trata paginação
    while "_links" in resposta and "next" in resposta["_links"]:
        proxima_url = resposta["_links"]["next"]["href"]
        resposta = obter_dados_api(proxima_url)
        if resposta and "_embedded" in resposta:
            itens.extend(resposta["_embedded"].get("item", []))
    
    return itens

# Parâmetros da licitação
uasg = 153177
numero_pregao = "90012"
ano = 2025

# Execução principal
if __name__ == "__main__":
    print("\n" + "="*80)
    print("UNIVERSIDADE TECNOLOGICA FEDERAL DO PARANA")
    print("UTFPR - CAMPUS SUDOESTE PATO BRANCO")
    print("="*80)
    
    # Etapa 1: Buscar licitação por UASG e número
    resultado_busca = buscar_licitacao_por_uasg_numero(uasg, numero_pregao, ano)
    
    if not resultado_busca or "_embedded" not in resultado_busca:
        print("\n⚠️ Licitação não encontrada na base de dados")
        print("Possíveis causas:")
        print("- Licitação ainda não publicada (futura)")
        print("- Formato diferente de numeração")
        print("- Dados indisponíveis na API aberta")
        exit()
    
    licitacoes = resultado_busca["_embedded"]["pregoes"]
    
    if not licitacoes:
        print("\n🚨 Nenhum pregão encontrado com os parâmetros fornecidos")
        exit()
    
    # Seleciona a primeira licitação encontrada
    licitacao = licitacoes[0]
    id_licitacao = licitacao["id"]
    print(f"\n✅ Licitação encontrada | ID: {id_licitacao}")
    
    # Etapa 2: Obter itens da licitação
    itens = obter_itens_licitacao(id_licitacao)
    
    if not itens:
        print("\n⚠️ Não foram encontrados itens para esta licitação")
        exit()
    
    # Processar informações básicas
    tem_beneficio_me = any(
        item.get("tipo_beneficio") in ["MICROEMPRESA", "EMPRESA_DE_PEQUENO_PORTE"] 
        for item in itens
    )
    
    # Exibir informações principais
    print(f"\nUASG: {uasg}")
    print(f"Pregão Eletrônico SRP {numero_pregao}/{ano}")
    print(f"Possui benefícios ME/EPP: {'Sim' if tem_beneficio_me else 'Não'}")
    
    if "data_abertura" in licitacao:
        print(f"Entrega até: {formatar_data(licitacao['data_abertura'])}")
    
    print("\n" + "-"*80)
    print(f"ITENS DA LICITAÇÃO ({len(itens)} encontrados):")
    print("-"*80)
    
    # Exibir itens simplificados
    for item in itens:
        print(f"\n▶ Item {item.get('numero')}: {item.get('descricao')}")
        print(f"  Quantidade: {item.get('quantidade')} {item.get('unidade', 'UN')}")
        print(f"  Valor estimado: R$ {item.get('valor_estimado', 0):.2f}")
        print(f"  Benefícios: {item.get('tipo_beneficio', 'Nenhum')}")
    
    print("\n" + "="*80)
    print(f"📋 Resumo: {len(itens)} itens listados com sucesso")
    print(f"🔗 Acesso direto: https://compras.dados.gov.br/pregoes/v1/pregoes/{id_licitacao}.json")
    print("="*80)
#!/usr/bin/env python3
"""
Script Final: Trello + Google Sheets
===================================

Script integrado para monitorar cards do Trello e atualizar planilha do Google Sheets
"""

import requests
import time
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# 🔐 Configurações da API Trello
API_KEY = '683cba47b43c3a1cfb10cf809fecb685'
TOKEN = 'ATTA89e63b1ce30ca079cef748f3a99cda25de9a37f3ba98c35680870835d6f2cae034C088A8'

# IDs das listas PREPARANDO encontradas
LISTAS_PREPARANDO = [
    '664652c058803ee88dac1f69',  # Board: Novo Pietro
    '6650f3369bb9bacb525d1dc8'   # Board: Pietro M. R.
]

# 📊 Configurações do Google Sheets
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18PjcswGwiK4xFp3t8rPEm_RrpoFVcvjmPdfBSIEzNRs/edit?gid=0#gid=0"
SPREADSHEET_ID = "18PjcswGwiK4xFp3t8rPEm_RrpoFVcvjmPdfBSIEzNRs"

# 🧠 Armazena os cards já processados
processed_cards = set()

def get_cards_in_list(list_id):
    """Busca todos os cards de uma lista específica"""
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {'key': API_KEY, 'tokens': TOKEN}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_all_preparando_cards():
    """Busca cards de todas as listas PREPARANDO"""
    all_cards = []
    for list_id in LISTAS_PREPARANDO:
        try:
            cards = get_cards_in_list(list_id)
            for card in cards:
                card['source_list_id'] = list_id  # Adiciona info da lista de origem
            all_cards.extend(cards)
            print(f"📋 {len(cards)} cards encontrados na lista {list_id}")
        except Exception as e:
            print(f"❌ Erro ao acessar lista {list_id}: {e}")
    return all_cards

def get_attachments(card_id):
    """Busca todos os anexos de um card"""
    url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    params = {'key': API_KEY, 'token': TOKEN}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def add_auth_to_url(url):
    """Adiciona credenciais na URL"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query['key'] = [API_KEY]
    query['token'] = [TOKEN]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def extract_data_from_txt(attachment_id, card_id):
    """Baixa e extrai dados do anexo .txt"""
    url = f"https://api.trello.com/1/cards/{card_id}/attachments/{attachment_id}"
    params = {'key': API_KEY, 'token': TOKEN}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Erro ao acessar anexo: {response.status_code}")
            return None
            
        attachment_info = response.json()
        download_url = attachment_info.get('url')
        
        if not download_url:
            print("❌ URL de download não encontrada")
            return None
        
        # Tenta diferentes métodos de autenticação
        methods = [
            lambda url: add_auth_to_url(url),
            lambda url: (url, {'Authorization': f'OAuth oauth_consumer_key="{API_KEY}", oauth_token="{TOKEN}"'}),
            lambda url: (url, {})
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                if isinstance(method(download_url), tuple):
                    test_url, headers = method(download_url)
                else:
                    test_url = method(download_url)
                    headers = {}
                
                headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "text/plain, */*;q=0.9",
                })
                
                download_response = requests.get(test_url, headers=headers)
                
                if download_response.status_code == 200:
                    content = download_response.text.strip()
                    lines = content.splitlines()
                    
                    print(f"📄 Conteúdo do arquivo .txt ({len(lines)} linhas):")
                    for idx, line in enumerate(lines):
                        print(f"  {idx}: {line}")
                    
                    data = extract_structured_data(lines)
                    return data
                    
            except Exception as e:
                continue
        
        print("❌ Todas as tentativas de download falharam")
        return None
        
    except Exception as e:
        print(f"❌ Erro geral no download: {e}")
        return None

def extract_structured_data(lines):
    """Extrai dados estruturados das linhas do arquivo .txt"""
    data = {
        'new_card_name': None,
        'dia_pregao': None,
        'uasg': None,
        'numero_pregao': None,
        'link_compras_gov': None,
        'downloads_pregao': None
    }
    
    try:
        # Novo nome do card (linhas 1, 2, 3)
        if len(lines) >= 4:
            data['new_card_name'] = f"{lines[1]}\\n{lines[2]}\\n{lines[3]}"
        
        print(f"\\n🔍 Extraindo dados estruturados:")
        
        # Extrai informações específicas
        for i, line in enumerate(lines):
            line = line.strip()
            
            # UASG
            if 'UASG' in line or 'Uasg' in line:
                uasg_match = re.search(r'(\d{6})', line)
                if uasg_match:
                    data['uasg'] = uasg_match.group(1)
                    print(f"  ✅ UASG: {data['uasg']}")
            
            # Número do pregão/dispensa
            if 'Pregão' in line or 'Dispensa' in line:
                pregao_match = re.search(r'(\d+/\d{4})', line)
                if pregao_match:
                    data['numero_pregao'] = pregao_match.group(1)
                    print(f"  ✅ Nº Pregão: {data['numero_pregao']}")
            
            # Link compras.gov
            if 'http' in line and 'compras' in line.lower():
                data['link_compras_gov'] = line.strip()
                print(f"  ✅ Link: {data['link_compras_gov']}")
            
            # Data (formato dd/mm/yyyy)
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
            if date_match:
                data['dia_pregao'] = date_match.group(1)
                print(f"  ✅ Data: {data['dia_pregao']}")
        
        return data
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados: {e}")
        return None

def update_card_name(card_id, new_name):
    """Atualiza o nome do card"""
    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        'key': API_KEY,
        'token': TOKEN,
        'name': new_name
    }
    response = requests.put(url, params=params)
    if response.status_code == 200:
        print(f"✅ Card atualizado com sucesso!")
        return True
    else:
        print(f"❌ Erro ao atualizar card. Status: {response.status_code}")
        return False

def get_compras_gov_links(card_id):
    """Busca links do compras.gov nos anexos do card"""
    attachments = get_attachments(card_id)
    compras_links = []
    
    for attachment in attachments:
        if attachment.get('url') and 'compras.gov' in attachment.get('url', ''):
            compras_links.append(attachment['url'])
    
    return compras_links

def generate_download_filename(uasg, numero_pregao):
    """Gera nome do arquivo: U_xxx_N_yyy_E.pdf"""
    if uasg and numero_pregao:
        numero_clean = numero_pregao.replace('/', '_')
        return f"U_{uasg}_N_{numero_clean}_E.pdf"
    return None

def register_in_spreadsheet(card_data, item_number):
    """Simula registro na planilha do Google Sheets"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    row_data = {
        'Item': item_number,
        'Timestamp': timestamp,
        'Dia Pregão': card_data.get('dia_pregao', ''),
        'UASG': card_data.get('uasg', ''),
        'Nº Pregão': card_data.get('numero_pregao', ''),
        'Link Compras.gov': card_data.get('link_compras_gov', ''),
        'Downloads Pregão': card_data.get('downloads_pregao', ''),
        'Proposta.csv': ''
    }
    
    print(f"\\n📊 Dados para planilha (Item {item_number}):")
    for key, value in row_data.items():
        print(f"   {key}: {value}")
    
    print("✅ Dados registrados na planilha (simulação)")
    return True

def process_all_cards():
    """Processa todos os cards das listas PREPARANDO"""
    print("🎯 Processando todos os cards das listas PREPARANDO...")
    
    try:
        all_cards = get_all_preparando_cards()
        print(f"\\n📋 Total de {len(all_cards)} cards encontrados")
        
        item_counter = 1
        
        for card in all_cards:
            print(f"\\n{'='*60}")
            print(f"🔎 Processando card {item_counter}: {card['name']}")
            print(f"   ID: {card['id']}")
            print(f"   Lista: {card['source_list_id']}")
            
            attachments = get_attachments(card['id'])
            txt_attachment = next((a for a in attachments if a['name'].endswith('.txt')), None)
            
            if txt_attachment:
                print(f"📎 Anexo .txt encontrado: {txt_attachment['name']}")
                
                # Extrai dados do arquivo .txt
                card_data = extract_data_from_txt(txt_attachment['id'], card['id'])
                
                if card_data and card_data['new_card_name']:
                    # Busca links do compras.gov
                    compras_links = get_compras_gov_links(card['id'])
                    if compras_links:
                        card_data['link_compras_gov'] = compras_links[0]
                        print(f"🔗 Link compras.gov encontrado nos anexos")
                    
                    # Gera nome do arquivo de download
                    download_filename = generate_download_filename(
                        card_data['uasg'], 
                        card_data['numero_pregao']
                    )
                    if download_filename:
                        card_data['downloads_pregao'] = download_filename
                        print(f"📁 Nome do arquivo: {download_filename}")
                    
                    # Registra na planilha
                    register_in_spreadsheet(card_data, item_counter)
                    
                    # Pergunta se quer atualizar o nome do card
                    try:
                        update_name = input(f"\\n🔄 Atualizar nome do card? (s/n): ").lower().strip()
                        if update_name in ['s', 'sim', 'y', 'yes']:
                            success = update_card_name(card['id'], card_data['new_card_name'])
                            if success:
                                processed_cards.add(card['id'])
                    except KeyboardInterrupt:
                        print("\\n⏭️ Pulando atualização do nome...")
                    
                    item_counter += 1
                    
                else:
                    print(f"⚠️ Não foi possível extrair dados válidos do .txt")
            else:
                print(f"⚠️ Nenhum anexo .txt encontrado no card")
                
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🚀 Script Final: Trello + Google Sheets")
    print("=" * 60)
    print("📋 Processando cards das listas PREPARANDO...")
    print("📊 Gerando dados para planilha do Google Sheets")
    print("=" * 60)
    
    process_all_cards()
    
    print(f"\\n{'='*60}")
    print("🏁 Processamento concluído!")
    print(f"📊 Planilha: {SPREADSHEET_URL}")
    print("\\nPara implementar a integração real com Google Sheets,")
    print("configure as credenciais de service account do Google Cloud.")


import os
import time
import shutil
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURAÇÕES ===
DOWNLOAD_TEMP_PATH = os.path.join(os.getcwd(), "downloads_temp")
EDITAL_DESTINO = r"C:\Users\pietr\Meu Drive\Arte Comercial\EDITAIS\Junho"
URL_EDITAL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra=16024905910272025"

# Extrair informações da URL para o nome do arquivo
def extrair_info_url(url):
    """Extrai número da compra da URL para formar o nome do arquivo"""
    match = re.search(r'compra=(\d+)', url)
    if match:
        numero_compra = match.group(1)
        # Formato: U_xxx_Nyyy onde xxx são os últimos 3 dígitos e yyy são os dígitos do meio
        if len(numero_compra) >= 6:
            xxx = numero_compra[-3:]  # Últimos 3 dígitos
            yyy = numero_compra[-6:-3]  # 3 dígitos anteriores aos últimos 3
            return f"U_{xxx}_N{yyy}"
    return "U_000_N000"

NOME_BASE_ARQUIVO = extrair_info_url(URL_EDITAL)

# Localizadores para o botão de download e menu
LOCALIZADORES_BOTAO_MENU = [
    # Botão principal que abre o menu
    (By.XPATH, "//button[.//i[contains(@class, 'fa-download')]]"),
    (By.XPATH, "//app-botao-relatorios-compra//button"),
    (By.CSS_SELECTOR, "app-botao-relatorios-compra button"),
    (By.XPATH, "//button[@mattooltip='Downloads relacionados a compra']"),
]

LOCALIZADORES_ITEM_MENU = [
    # Item específico do menu
    (By.XPATH, "/html/body/div[3]/ul/li[1]/div/a/span"),
    (By.XPATH, "//span[contains(text(), 'Condições da aquisição ou contratação')]"),
    (By.XPATH, "//span[@class='p-menuitem-text ng-star-inserted'][contains(text(), 'Condições')]"),
    (By.CSS_SELECTOR, "span.p-menuitem-text.ng-star-inserted"),
    (By.XPATH, "//div[contains(@class, 'p-menuitem')]//span[contains(text(), 'Condições')]"),
]

# === CONFIGURAR CHROME ===
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_TEMP_PATH,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True,
    "profile.default_content_settings.popups": 0,
    "profile.default_content_setting_values.automatic_downloads": 1
})

# Flags para melhor performance e menos erros
chrome_options.add_argument("--disable-3d-apis")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--silent")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Para debug, remova o comentário da linha abaixo
# chrome_options.add_argument("--headless=new")

os.makedirs(DOWNLOAD_TEMP_PATH, exist_ok=True)
os.makedirs(EDITAL_DESTINO, exist_ok=True)

def aguardar_download(pasta, timeout=60):
    """Aguarda um arquivo ser baixado completamente"""
    inicio = time.time()
    while time.time() - inicio < timeout:
        arquivos = os.listdir(pasta)
        # Procurar arquivos que não sejam temporários (.crdownload, .tmp)
        arquivos_completos = [f for f in arquivos if not f.endswith(('.crdownload', '.tmp', '.part'))]
        if arquivos_completos:
            return arquivos_completos[0]
        time.sleep(1)
    return None

driver = None
try:
    print("🚀 Iniciando navegador...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    print("🌐 Navegando para a página do edital...")
    driver.get(URL_EDITAL)
    
    print("⏳ Aguardando carregamento da aplicação Angular...")
    wait = WebDriverWait(driver, 45)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "app-root")))
    
    # Aguardar carregamento completo
    time.sleep(8)
    
    print("🔍 Procurando botão de downloads...")
    botao_menu_encontrado = False
    
    # Primeiro, encontrar e clicar no botão que abre o menu
    for i, (by, locator) in enumerate(LOCALIZADORES_BOTAO_MENU):
        try:
            print(f"   Tentativa {i+1}: Procurando botão do menu...")
            botao_menu = wait.until(EC.element_to_be_clickable((by, locator)))
            
            # Rolar até o elemento
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", botao_menu)
            time.sleep(2)
            
            # Clicar no botão para abrir o menu
            try:
                botao_menu.click()
            except:
                driver.execute_script("arguments[0].click();", botao_menu)
            
            print("✅ Botão do menu clicado! Aguardando menu aparecer...")
            botao_menu_encontrado = True
            time.sleep(3)  # Aguardar menu aparecer
            break
            
        except Exception as e:
            print(f"❌ Tentativa {i+1} falhou: {str(e)[:60]}...")
            continue
    
    if not botao_menu_encontrado:
        raise Exception("Não foi possível encontrar o botão que abre o menu de downloads.")
    
    print("🎯 Procurando item 'Condições da aquisição ou contratação' no menu...")
    item_encontrado = False
    
    # Agora procurar o item específico no menu
    for i, (by, locator) in enumerate(LOCALIZADORES_ITEM_MENU):
        try:
            print(f"   Tentativa {i+1}: Procurando item do menu...")
            
            # Aguardar o item aparecer no menu
            item_menu = wait.until(EC.element_to_be_clickable((by, locator)))
            
            # Verificar se o texto está correto
            texto_item = item_menu.text
            print(f"   Item encontrado: '{texto_item}'")
            
            # Clicar no item
            try:
                item_menu.click()
            except:
                # Se não conseguir clicar diretamente, tentar com ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(item_menu).click().perform()
            
            print("✅ Item do menu clicado! Iniciando download...")
            item_encontrado = True
            break
            
        except Exception as e:
            print(f"❌ Tentativa {i+1} falhou: {str(e)[:60]}...")
            continue
    
    if not item_encontrado:
        print("🔍 Debug: Procurando todos os itens de menu disponíveis...")
        try:
            # Tentar encontrar todos os itens do menu para debug
            itens_menu = driver.find_elements(By.XPATH, "//div[contains(@class, 'p-menu')]//span")
            print(f"Encontrados {len(itens_menu)} itens de menu:")
            for j, item in enumerate(itens_menu[:10]):  # Mostrar apenas os primeiros 10
                try:
                    texto = item.text.strip()
                    if texto:
                        print(f"   Item {j+1}: '{texto}'")
                except:
                    pass
        except:
            pass
        
        raise Exception("Não foi possível encontrar o item 'Condições da aquisição ou contratação' no menu.")
    
    print("⏬ Aguardando download do arquivo...")
    
    # Aguardar o download ser concluído
    arquivo_baixado = aguardar_download(DOWNLOAD_TEMP_PATH, timeout=90)
    
    if not arquivo_baixado:
        print("📂 Verificando conteúdo da pasta de download...")
        todos_arquivos = os.listdir(DOWNLOAD_TEMP_PATH)
        for arquivo in todos_arquivos:
            print(f"   - {arquivo}")
        raise FileNotFoundError("Nenhum arquivo foi baixado ou o download não foi concluído.")
    
    print(f"📄 Arquivo baixado: {arquivo_baixado}")
    
    # Mover e renomear o arquivo
    caminho_origem = os.path.join(DOWNLOAD_TEMP_PATH, arquivo_baixado)
    extensao = os.path.splitext(arquivo_baixado)[1]
    nome_final = NOME_BASE_ARQUIVO + extensao
    caminho_destino = os.path.join(EDITAL_DESTINO, nome_final)
    
    # Verificar se arquivo já existe e criar nome único se necessário
    contador = 1
    caminho_destino_original = caminho_destino
    while os.path.exists(caminho_destino):
        nome_com_contador = f"{NOME_BASE_ARQUIVO}_{contador}{extensao}"
        caminho_destino = os.path.join(EDITAL_DESTINO, nome_com_contador)
        contador += 1
    
    shutil.move(caminho_origem, caminho_destino)
    
    print(f"✅ Arquivo salvo com sucesso!")
    print(f"📁 Nome original: {arquivo_baixado}")
    print(f"📁 Nome final: {os.path.basename(caminho_destino)}")
    print(f"📁 Localização: {caminho_destino}")

except Exception as e:
    print(f"❌ Erro durante a execução: {e}")
    
    # Salvar informações de debug em caso de erro
    if driver:
        try:
            print("💾 Salvando informações de debug...")
            driver.save_screenshot("debug_screenshot.png")
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("   Screenshot salvo: debug_screenshot.png")
            print("   HTML salvo: debug_page_source.html")
        except:
            pass

finally:
    if driver:
        driver.quit()
        print("🔚 Driver encerrado.")
    
    # Limpar pasta temporária
    try:
        if os.path.exists(DOWNLOAD_TEMP_PATH):
            shutil.rmtree(DOWNLOAD_TEMP_PATH)
    except:
        pass

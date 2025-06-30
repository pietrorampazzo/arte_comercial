import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURAÇÕES ===
DOWNLOAD_TEMP_PATH = os.path.join(os.getcwd(), "downloads_temp")
EDITAL_DESTINO = r"C:\Users\pietr\Meu Drive\Arte Comercial\EDITAIS\Junho"
URL_EDITAL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra=16024905910272025"

# Múltiplas opções de localização do botão
LOCALIZADORES_BOTAO = [
    # XPath baseado no ícone fa-download (mais robusto)
    (By.XPATH, "//i[contains(@class, 'fa-download')]/ancestor::button"),
    
    # XPath completo corrigido
    (By.XPATH, "/html/body/app-root/div/div/div/app-cabecalho-compra-acesso-publico/app-cabecalho-compra/div[4]/div[2]/div/app-botoes-cabecalho-compra/span/span/app-botao-relatorios-compra/span/app-botao-icone/span/button"),
    
    # CSS Selector
    (By.CSS_SELECTOR, "app-botao-relatorios-compra app-botao-icone button"),
    
    # XPath mais flexível
    (By.XPATH, "//app-botao-relatorios-compra//button"),
    
    # XPath pelo componente Angular
    (By.XPATH, "//app-botao-icone//button[.//i[contains(@class, 'fa-download')]]")
]

# === CONFIGURAR CHROME ===
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_TEMP_PATH,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
})
# Remova o headless para debug
# chrome_options.add_argument("--headless=new")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')

os.makedirs(DOWNLOAD_TEMP_PATH, exist_ok=True)

driver = None
try:
    print("Iniciando navegador...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(URL_EDITAL)
    print("Página carregada. Aguardando carregamento completo...")
    
    # Aguardar carregamento da página Angular
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "app-root")))
    
    # Aguardar um pouco mais para componentes Angular carregarem
    time.sleep(15)
    
    print("Tentando localizar o botão de download...")
    botao_encontrado = False
    
    # Tentar cada localizador
    for i, (by, locator) in enumerate(LOCALIZADORES_BOTAO):
        try:
            print(f"Tentativa {i+1}: {locator}")
            botao = wait.until(EC.element_to_be_clickable((by, locator)))
            
            # Rolar até o elemento se necessário
            driver.execute_script("arguments[0].scrollIntoView(true);", botao)
            time.sleep(1)
            
            # Tentar clicar
            botao.click()
            print(f"✅ Botão encontrado e clicado com: {locator}")
            botao_encontrado = True
            break
            
        except Exception as e:
            print(f"❌ Tentativa {i+1} falhou: {str(e)[:100]}...")
            continue
    
    if not botao_encontrado:
        # Debug: salvar informações para análise
        print("Salvando informações de debug...")
        driver.save_screenshot("debug_screenshot.png")
        
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Tentar encontrar elementos relacionados para debug
        elementos_debug = [
            "//i[contains(@class, 'fa-download')]",
            "//app-botao-relatorios-compra",
            "//app-botao-icone",
            "//button"
        ]
        
        for xpath in elementos_debug:
            try:
                elementos = driver.find_elements(By.XPATH, xpath)
                print(f"Encontrados {len(elementos)} elementos para: {xpath}")
            except:
                pass
        
        raise Exception("Botão de download não encontrado. Verifique os arquivos de debug.")
    
    print("Aguardando download iniciar...")
    time.sleep(15)
    
    # Verificar se arquivos foram baixados
    arquivos_baixados = [f for f in os.listdir(DOWNLOAD_TEMP_PATH) if f.endswith(('.pdf', '.zip'))]
    if not arquivos_baixados:
        raise FileNotFoundError("Nenhum arquivo PDF ou ZIP foi baixado.")
    
    nome_arquivo = arquivos_baixados[0]
    caminho_origem = os.path.join(DOWNLOAD_TEMP_PATH, nome_arquivo)
    
    # Nome final
    nome_final = "U_160249_N_91027_E" + os.path.splitext(nome_arquivo)[1]
    caminho_destino = os.path.join(EDITAL_DESTINO, nome_final)
    
    shutil.move(caminho_origem, caminho_destino)
    print(f"✅ Arquivo salvo em: {caminho_destino}")

except Exception as e:
    print(f"❌ Erro: {e}")

finally:
    if driver:
        driver.quit()
        print("Driver encerrado.")

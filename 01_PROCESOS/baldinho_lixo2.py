import os
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURAÇÕES ===
DOWNLOAD_TEMP_PATH = os.path.join(os.getcwd(), "downloads_temp")
EDITAL_DESTINO = r"C:\Users\pietr\Meu Drive\Arte Comercial\EDITAIS\Junho"
URL_EDITAL = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/acompanhamento-compra?compra=16024905910272025"

# Configurar Chrome com seu perfil existente
chrome_options = Options()

# IMPORTANTE: Feche todas as janelas do Chrome antes de executar
# Caminho para seus dados do Chrome (ajuste conforme necessário)
user_data_dir = r"C:\Users\pietr\AppData\Local\Google\Chrome\User Data"
profile_directory = "Default"  # ou "Profile 1", "Profile 2", etc.

chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument(f"--profile-directory={profile_directory}")

# Configurações de download
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_TEMP_PATH,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True
})

# Manter o navegador aberto após o script
chrome_options.add_experimental_option("detach", True)

os.makedirs(DOWNLOAD_TEMP_PATH, exist_ok=True)

driver = None
try:
    print("🚀 Iniciando Chrome com seu perfil...")
    print("⚠️  IMPORTANTE: Feche todas as janelas do Chrome antes de continuar!")
    input("Pressione Enter quando tiver fechado o Chrome...")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )
    
    print("✅ Chrome iniciado com seu perfil!")
    print("🌐 Navegando para ComprasNet...")
    
    driver.get(URL_EDITAL)
    
    # Resto do seu código aqui...
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print("\n💡 Dicas para resolver:")
    print("1. Feche TODAS as janelas do Chrome")
    print("2. Verifique se o caminho do perfil está correto")
    print("3. Tente usar um perfil diferente")

finally:
    # Não feche o driver automaticamente para manter o perfil
    if driver:
        print("🔄 Navegador permanecerá aberto...")

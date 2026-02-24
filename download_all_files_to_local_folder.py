import traceback
from sharepoint_api import SharePointClient
from dotenv import load_dotenv
import os
import pandas as pd

# Carregar variáveis de ambiente
load_dotenv()

# Configuração das chaves de ambiente
tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
site_url = os.getenv('SITE_URL')
resource = os.getenv('RESOURCE')

# Inicializar cliente SharePoint
client = SharePointClient(tenant_id, client_id, client_secret, resource)

# Obter ID do site
try:
    site_id = client.get_site_id(site_url)
except Exception as e:
    print(f"Error getting site ID: {e}")
    exit(1)

# Obter informações do drive
try:
    drive_info = client.get_drive_id(site_id)
    drive_id = drive_info[0]['id']  # Assume o primeiro ID de drive
    print(f"Drive ID: {drive_id}")
    
except Exception as e:
    print(f"Error getting drive ID: {e}")
    exit(1)
sharepoint_path = "02- Procedimentos/Operação XLA/Tegma"
local_save_path = "documentos_oficiais"

# client.download_all_files(site_id, drive_id, local_save_path) # Comente esta linha que baixa da raiz

# se você quiser baixar de um caminho específico
client.download_all_files(site_id, drive_id, local_save_path, sharepoint_path, extensions=['.pdf']) # Descomente esta linha
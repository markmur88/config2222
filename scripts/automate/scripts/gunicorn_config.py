import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Definir BASE_DIR
BASE_DIR = Path(__file__).resolve().parent

bind = f"{os.getenv('URL', '127.0.0.1')}:{os.getenv('PORT', '8000')}"
workers = 3
certfile = os.path.join(BASE_DIR, 'keys/cert.pem')
keyfile = os.path.join(BASE_DIR, 'keys/key.pem')

# Verificar si los archivos de certificado y clave existen
if not os.path.isfile(certfile):
    raise FileNotFoundError(f"Certificado no encontrado: {certfile}")
if not os.path.isfile(keyfile):
    raise FileNotFoundError(f"Clave no encontrada: {keyfile}")
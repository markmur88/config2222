import uuid
import requests
import json
from datetime import datetime
import os
import sys
import time
from send.utils import correlation_id, get_otp, check_required_headers, generate_uuid, generate_end_to_end_identification  # Importar función necesaria
from send.data import DATA, API_URL # Importar swift_data

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS_PATH = os.path.join(BASE_DIR, "headers.json")

# Leer los headers desde el archivo headers.json
with open(HEADERS_PATH, 'r') as file:
    headers = json.load(file)

# Agregar headers requeridos
paymentId = generate_uuid()
headers.update({
    'idempotency-id': f"DET{paymentId}",  # Usar la función importada
    'processId': generate_uuid(),  # Usar la función importada
    'otp': get_otp(),
    'Correlation-Id': correlation_id(paymentId),  # Usar la función importada
    'Origin': 'https://ebankingdb2.db.com/private/index.do?loggedon&locate-end&valid_4915.9867.7236.24',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type',
    'Cookie': 'SESSION_ID=SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880',
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Strict-Transport-Security': 'max-age=3628800; includeSubDomains',
    'previewsignature': 'CR38828530'
})

# Verificar headers requeridos
check_required_headers(headers)

# Obtener la IP del argumento
if len(sys.argv) != 2:
    print("Uso: python send_swift.py <ip>")
    sys.exit(1)

ip = sys.argv[1]

# URL del endpoint que recibe el JSON
api_url = API_URL

# Enviar el JSON con reintentos
max_retries = 3
retry_delay = 5  # segundos

for attempt in range(max_retries):
    try:
        DATA["endToEndIdentification"] = generate_end_to_end_identification(paymentId)
        response = requests.post(api_url, json=DATA, headers=headers)
        if response.status_code == 200:
            print("Transferencia SWIFT enviada exitosamente.")
            print("Respuesta del servidor:", response.json())
            break
        else:
            print("Error al enviar la transferencia SWIFT.")
            print("Código de estado:", response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar la transferencia SWIFT: {e}")
        if attempt < max_retries - 1:
            print(f"Reintentando en {retry_delay} segundos...")
            time.sleep(retry_delay)
        else:
            print("Máximo número de reintentos alcanzado. No se pudo enviar la transferencia SWIFT.")
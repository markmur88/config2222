import json
import sys
import time
import uuid
import base64
import os
import hashlib
import logging
import requests
import ssl
from datetime import datetime
from send.utils import generate_end_to_end_identification, correlation_id, check_required_headers, generate_uuid
from config import CERT_PATH  # Importar CERT_PATH
from constants import paymentId  # Importar paymentId desde constants.py

# Configuración de logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error_logger")


def enviar_transaccion(ip: str, usuario: str, clave: str, estado: str, paymentId: str) -> None:
    from send.data import API_URL, DATA  # Mover la importación aquí
    transaccion = DATA.copy()
    transaccion.update({
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ip_servidor": ip,
        "usuario": usuario,
        "clave": clave,
        "estado": estado,
        "paymentId": paymentId,
        "idempotency-id": f"DEUT{paymentId}",
        "Correlation-Id": f"RET{paymentId}",
        "endToEndIdentification": paymentId
    })
    logger.info("Enviando transacción JSON:")
    logger.info(json.dumps(transaccion, indent=4))

    api_url = API_URL
    max_retries = 3
    retry_delay = 5  # segundos

    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=transaccion, headers={"Content-Type": "application/json"}, cert=CERT_PATH)
            if response.status_code == 200:
                logger.info("Transferencia SWIFT enviada exitosamente.")
                logger.info(f"Respuesta del servidor: {response.json()}")
                break
            else:
                error_logger.error(f"Error al enviar la transferencia SWIFT. Código de estado: {response.status_code}")
                if response.status_code == 401:
                    error_logger.error("Error 401: No autorizado. Verifique las credenciales o el token.")
        except requests.exceptions.SSLError as ssl_error:
            error_logger.error(f"Error SSL al enviar la transferencia SWIFT: {ssl_error}")
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logger.error("Máximo número de reintentos alcanzado. No se pudo enviar la transferencia SWIFT.")
        except requests.exceptions.RequestException as e:
            error_logger.error(f"Error al enviar la transferencia SWIFT: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logger.error("Máximo número de reintentos alcanzado. No se pudo enviar la transferencia SWIFT.")


def get_otp(paymentId):
    from send.data import API_URL, DATA  # Mover la importación aquí
    correlation_id_value = f"RET{paymentId}"
    headers = {
        'Correlation-Id': correlation_id_value 
    } 
    data = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {
            "targetIban": DATA["creditorAccount"]["iban"],
            "amountCurrency": DATA["instructedAmount"]["currency"],
            "amountValue": DATA["instructedAmount"]["amount"]
        }
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response_data = response.json()
    return response_data.get('otp', '')

def main():
    from send.data import API_URL, DATA  # Mover la importación aquí
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    HEADERS_PATH = os.path.join(BASE_DIR, "headers.json")
    with open(HEADERS_PATH, 'r') as file:
        headers = json.load(file)

    paymentId = paymentId
    headers.update({
        'idempotency-id': f"DET{paymentId}",
        'processId': generate_uuid(),
        'otp': get_otp(paymentId),
        'Correlation-Id': correlation_id(paymentId),
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

    check_required_headers(headers)

    if len(sys.argv) != 2:
        print("Uso: python swift.py <ip>")
        sys.exit(1)

    ip = sys.argv[1]
    api_url = API_URL
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

if __name__ == "__main__":
    main()

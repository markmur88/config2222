import json
import time
import token
import uuid
import base64
import os
import hashlib
from datetime import datetime
import logging  # Importar logging

import requests
from send.data import API_URL, DATA  # Importar DATA desde data.py
from send.utils import generate_end_to_end_identification, correlation_id, check_required_headers, generate_uuid  # Importar funciones necesarias
from config import CERT_PATH  # Importar CERT_PATH

# Configuración de logging
logger = logging.getLogger(__name__)
error_logger = logging.getLogger("error_logger")

def get_otp():
    correlation_id = correlation_id()  # Usar la función importada
    headers = {
        'Correlation-Id': correlation_id 
    } 
    data = {
        "method": "PUSHTAN",
        "requestType": "SEPA_CREDIT_TRANSFERS",
        "requestData": {
            "targetIban": DATA["creditorAccount"]["iban"],
            "amountCurrency": DATA["instructedAmount"]["currencyCode"],
            "amountValue": DATA["instructedAmount"]["amount"]
        }
    }
    response = requests.post('https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges', headers=headers, json=data)
    response_data = response.json()
    return response_data.get('otp', '')

headers = {
    'Authorization': f'Bearer {token}',
    'idempotency-id': generate_uuid(),  # Usar la función importada
    'processId': generate_uuid(),  # Usar la función importada
    'otp': get_otp(),
    'Correlation-Id': correlation_id(),  # Usar la función importada
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
}

check_required_headers(headers)

data = {
    "debtorAccount": DATA["debtorAccount"],
    "instructedAmount": DATA["instructedAmount"],
    "creditorName": DATA["creditorName"],
    "creditorAccount": DATA["creditorAccount"],
    "creditorBank": DATA["creditorBank"],
    "creditorAgent": DATA["creditorAgent"],
    "creditorAddress": DATA["creditorAddress"],
    "debtorName": DATA["debtorName"],
    "debtorBank": DATA["debtorBank"],
    "debtorAgent": DATA["debtorAgent"],
    "debtorAddress": DATA["debtorAddress"],
    "remittanceInformationUnstructured": DATA["remittanceInformationUnstructured"],
    "date": DATA["date"],
    "paymentType": DATA["paymentType"],
    "endToEndIdentification": generate_end_to_end_identification()
}

def enviar_transaccion(ip: str, usuario: str, clave: str, estado: str, paymentId: str) -> None:
    transaccion = DATA.copy()
    transaccion.update({
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ip_servidor": ip,
        "usuario": usuario,
        "clave": clave,
        "estado": estado,
        "paymentId": paymentId,
        "idempotency-id": f"DET{paymentId}",
        "Correlation-Id": f"RET{paymentId}",
        "endToEndIdentification": paymentId
    })
    logger.info("Enviando transacción JSON:")
    logger.info(json.dumps(transaccion, indent=4))

    # Enviar el JSON con reintentos
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
        except requests.exceptions.RequestException as e:
            error_logger.error(f"Error al enviar la transferencia SWIFT: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                logger.error("Máximo número de reintentos alcanzado. No se pudo enviar la transferencia SWIFT.")

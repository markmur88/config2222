import requests
from config import settings
import logging

from api.core.auth_services import get_deutsche_bank_token, get_memo_bank_token

logger = logging.getLogger("bank_services")

def memo_bank_transfer(source_account, destination_account, amount, currency, idempotency_key):
    url = f"{settings.MEMO_BANK_API_URL}/transfers"
    headers = {
        "Authorization": f"Bearer {get_memo_bank_token()['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    payload = {
        "source_account": source_account,
        "destination_account": destination_account,
        "amount": str(amount),
        "currency": currency
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza un error si el status code no es 2xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Memo Bank: {e}, Response: {response.text}")
        return {"error": "Error en Memo Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Memo Bank: {e}")
        return {"error": "No se pudo conectar con Memo Bank"}


def deutsche_bank_transfer(idempotency_key, sender_name, sender_iban, sender_bic, recipient_name, recipient_iban, recipient_bic, status, amount, currency, execution_date):
    url = f"{settings.DEUTSCHE_BANK_API_URL}"
    headers = {
        "Authorization": f"Bearer {get_deutsche_bank_token()['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    payload = {
        "sender_name": sender_name,
        "sender_iban": sender_iban,
        "sender_bic": sender_bic,
        "recipient_name": recipient_name,
        "recipient_iban": recipient_iban,
        "recipient_bic": recipient_bic,
        "amount": str(amount),
        "currency": currency,
        "status": status,
        "execution_date": execution_date
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza un error si el status code no es 2xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": "Error en Deutsche Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": "No se pudo conectar con Deutsche Bank"}
    
    
def sepa_transfer(idempotency_key, sender_name, sender_iban, sender_bic, recipient_name, recipient_iban, recipient_bic, status, amount, currency, execution_date):
    url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
    headers = {
        "Authorization": f"Bearer {get_deutsche_bank_token()['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    payload = {
        "sender_name": sender_name,
        "sender_iban": sender_iban,
        "sender_bic": sender_bic,
        "recipient_name": recipient_name,
        "recipient_iban": recipient_iban,
        "recipient_bic": recipient_bic,
        "amount": str(amount),
        "currency": currency,
        "status": status,
        "execution_date": execution_date
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza un error si el status code no es 2xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": "Error en Deutsche Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": "No se pudo conectar con Deutsche Bank"}
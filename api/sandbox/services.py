from api.sandbox.models import IncomingCollection

def process_incoming_collection(data):
    """
    Procesa una colección entrante y la guarda en la base de datos.
    """
    collection = IncomingCollection.objects.create(**data)
    
    # Simulación de confirmación de pago en sandbox
    collection.status = "COMPLETED"
    collection.save()
    
    return collection

import requests
from config import settings

def get_account_balance(account_id):
    """
    Obtiene el balance de la cuenta desde Deutsche Bank (o sandbox).
    """
    url = f"{settings.DEUTSCHE_BANK_API_URL}/accounts/{account_id}/balance"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    
    return {"error": "No se pudo obtener el balance"}

def initiate_sepa_transfer(data):
    """
    Simula una transferencia SEPA con Deutsche Bank.
    """
    url = f"{settings.DEUTSCHE_BANK_API_URL}/sepa/transfer"
    response = requests.post(url, json=data)

    if response.status_code == 201:
        return response.json()
     
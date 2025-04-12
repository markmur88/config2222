import requests
from config import settings

def get_memo_bank_token():
    url = f"{settings.MEMO_BANK_API_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.MEMO_BANK_CLIENT_ID,
        "client_secret": settings.MEMO_BANK_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}


def get_deutsche_bank_token():
    url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.DEUTSCHE_BANK_CLIENT_ID,
        "client_secret": settings.DEUTSCHE_BANK_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}

import requests
from config import settings

def memo_bank_request(endpoint, payload, headers=None):
    url = f"{settings.MEMO_BANK_API_URL}/{endpoint}"
    headers = headers or {}
    headers.update({
        "Authorization": f"Bearer {settings.MEMO_BANK_CLIENT_SECRET}",
        "Content-Type": "application/json"
    })
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
    

def deutsche_bank_request(endpoint, payload, headers=None):
    url = f"{settings.DEUTSCHE_BANK_API_URL}/{endpoint}"
    headers = headers or {}
    headers.update({
        "Authorization": f"Bearer {settings.DEUTSCHE_BANK_CLIENT_SECRET}",
        "Content-Type": "application/json"
    })
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def get_memo_bank_accounts(token):
    url = f"{settings.MEMO_BANK_API_URL}/accounts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}

def get_deutsche_bank_accounts(token):
    url = f"{settings.DEUTSCHE_BANK_API_URL}/accounts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}

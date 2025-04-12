import os
import requests

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Obtener tokens desde variables de entorno
ACCESS_TOKEN = {
    "refresh": os.getenv("REFRESH_TOKEN"),
    "access": os.getenv("ACCESS_TOKEN"),
}

def get_access_token(refresh_token):
    """Obtiene un nuevo token de acceso usando el token de actualización."""
    url = "http://127.0.0.1:8000/api/auth/token/refresh/"
    response = requests.post(url, data={"refresh": refresh_token})
    if response.status_code == 200:
        return response.json().get("access")
    else:
        raise Exception(f"Error al refrescar el token: {response.status_code}")

# Uso del token
try:
    access_token = get_access_token(ACCESS_TOKEN["refresh"])
    print(f"Nuevo token de acceso: {access_token}")
except Exception as e:
    print(f"Error: {e}")
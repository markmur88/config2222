import jwt
import datetime

# Clave secreta para firmar el token
SECRET_KEY = 'bar1588623'

# Datos que se incluirán en el token
payload = {
    'sub': 'DE86500700100925993805',
    'name': 'MIRYA TRADING CO LTD',
    'iat': datetime.datetime.utcnow(),
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # El token expira en 24 horas
}

# Generar el token JWT
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')


with open('generated_token.txt', 'w') as token_file:
    token_file.write(token)

print(f"Generated JWT Token: {token}")

import jwt
from datetime import datetime, timedelta

def generar_token(user_id):
    with open('/private.pem', 'r') as f:
        private_key = f.read()
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token
 
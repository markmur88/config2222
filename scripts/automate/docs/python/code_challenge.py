import hashlib
import base64

# Usa el code_verifier generado anteriormente
code_verifier = "BR1s4ziHt5uYKwyat0ryEzw5v6L3-EJZDQbMjwhMIl-yBI0QULPW3g"
# Genera el code_challenge usando SHA-256 y codificación base64
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
print(code_challenge)
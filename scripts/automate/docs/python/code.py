import os
import base64
import hashlib

# Generar el code_verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
print("Code Verifier:", code_verifier)

# Generar el code_challenge
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
print("Code Challenge:", code_challenge)
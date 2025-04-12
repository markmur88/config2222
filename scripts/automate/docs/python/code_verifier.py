import os
import base64

# Generar una cadena aleatoria de 40 bytes y codificarla en base64
code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
print(code_verifier)
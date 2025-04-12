import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    import os
    os.system('pip install python-dotenv')
    from dotenv import load_dotenv
    load_dotenv()


URL_DB = "193.150.166.0"
PORT_DB = "22"
URL = "127.0.0.1"
PORT = "8000"
USERNAME = "493069k1"
PASSWORD = "54082"
CORREO = "j.moltke@db.com"
RED = "https://api-db-swift.onrender.com"

method = "pushTAN"
requestType = "INSTANT_SEPA_CREDIT_TRANSFERS"
targetIban = "ES9400496103962716120773"
targetSwiftBic = "BSCHESMMXXX"
amountCurrency = "EUR"
amountValue = 460000.00

from scripts import codeS256

# Ejecutar el script codeS256.py y obtener el nuevo valor de otp
code_verifier = codeS256.code_verifier
code_challenge = codeS256.code_challenge

otp = code_challenge


## Códigos Importantes
AUTHORIZATION_PIN = "02569S"
RELEASE_CODE = "DEUT4JV9XLTR5"
INTERBANK_BLOCKING_CODE_REQUIRED = "144A:S:G4639DV8"

# ONE TIME SATELLITE SWIFT DOWNLOAD ACCESS WITHDRAWAL CODE : 9573020414B9.0XC4329637ED9DB984
SENDER_IPWED = 'https://IPBANKINGDB2.DB.COM/PRIVATE/INDEX.DO?LOGGEDON&LOCATE-END&VALID_4915.9867.7236.24'
# Token de autenticación Bearer
BEARER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
CLIENT_SECRET  = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'
BANCO_ORIGEN = 'Deutsche Bank AG'




##URLS##
BANK_URL = "https://193.150.166.0:22/gw/dbapi/banking/transactions/v2"
#BANK_URL = "https://api.db.com/swift/transfer"
BANK_API_URL = f"https://{URL_DB}:{PORT_DB}/gw/dbapi/banking/transactions/v2"
SWIFT_TRANSFER_URL_LOCAL = f"https://{URL_DB}:{PORT_DB}/transferencia/"
SWIFT_TRANSFER_URL_RED = f"{RED}/transferencia/"

SWIFT_TRANSFER_URL = BANK_API_URL




##TOKEN##
SWIFT_URL_TOKEN_LOCAL = f"https://{URL}:{PORT}/o/token/"
SWIFT_URL_TOKEN_RED = f"{RED}/o/token/"
SWIFT_URL_TOKEN = SWIFT_URL_TOKEN_RED

SWIFT_URL_REFRESH_TOKEN_LOCAL = f"https://{URL}:{PORT}/o/token/refresh/"
SWIFT_URL_REFRESH_TOKEN_RED = f"{RED}/o/token/refresh/"
SWIFT_URL_REFRESH_TOKEN = SWIFT_URL_REFRESH_TOKEN_RED

SWIFT_URL_REVOKE_TOKEN_LOCAL = f"https://{URL}:{PORT}/o/token/revoke/"
SWIFT_URL_REVOKE_TOKEN_RED = f"{RED}/o/token/revoke/"
SWIFT_URL_REVOKE_TOKEN = SWIFT_URL_REVOKE_TOKEN_RED


DEUTSCHE_BANK_API = {
    'BASE_URL': 'https://api.db.com/v1/',  # URL base de las APIs de Deutsche Bank
    'CLIENT_ID': os.getenv('DB_CLIENT_ID', 'CLIENT_ID'),
    'CLIENT_SECRET': os.getenv('DB_CLIENT_SECRET', 'CLIENT_SECRET'),
    'USE_SSL': True,  # Indica si se debe utilizar SSL/TLS
}

SWIFT_SETTINGS = {
    'USE_LOCAL_SERVER': os.getenv('SWIFT_USE_LOCAL_SERVER', 'True').lower() == 'true',
    'SERVER_URL': os.getenv('SWIFT_SERVER_URL', 'URL'),
    'SERVER_PORT': os.getenv('SWIFT_SERVER_PORT', 'PORT'),
    'USE_SSL': os.getenv('SWIFT_USE_SSL', 'False').lower() == 'false',
    'USERNAME': os.getenv('SWIFT_USERNAME', 'USERNAME'),
    'PIN': os.getenv('SWIFT_PIN', 'PASSWORD'),
    'AUTH_TOKEN': os.getenv('SWIFT_AUTH_TOKEN', 'BEARER_TOKEN'),
    'INTERBANK_BLOCKING_CODE_REQUIRED': os.getenv('SWIFT_INTERBANK_BLOCKING_CODE_REQUIRED', 'False').lower() == 'true',
    'BANK_API_URL': os.getenv('BANK_API_URL', 'BANK_URL'),
    'BANK_API_KEY': os.getenv('BANK_API_KEY', 'tu_clave_api'),
    'BANK_CLIENT_ID': os.getenv('BANK_CLIENT_ID', 'CLIENT_ID'),
    'BANK_CLIENT_SECRET': os.getenv('BANK_CLIENT_SECRET', 'CLIENT_SECRET'),
}




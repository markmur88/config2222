from rest_framework.exceptions import APIException
import logging  # Importar el módulo de logging
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from django.conf import settings
import requests
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics

from api.sct.models import SepaCreditTransferRequest
from api.sct.serializers import SepaCreditTransferRequestSerializer
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml

from dotenv import load_dotenv
load_dotenv()


# Configurar el logger
logger = logging.getLogger(__name__)

# Constantes
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def deutsche_bank_transfer11(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # token_response = get_deutsche_bank_token()
        # access_token = token_response.get("access_token")
        
        access_token = os.getenv("ACCESS_TOKEN")

        
        # if not access_token:
        #     logger.error(f"Error obteniendo token de Deutsche Bank: {token_response.get('error', 'Respuesta desconocida')}")
        #     return {"error": "No se pudo obtener el token de acceso de Deutsche Bank"}

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            # "otp": "SEPA_TRANSFER_GRANT"
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            # 'PSU-ID': 'YOUR_USER_ID',
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'            
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode":transfer_request.purpose_code,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":transfer_request.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        SepaCreditTransferUpdateScaRequest = {
            "action": "CREATE",
            "authId":transfer_request.auth_id,
        }

        SepaCreditTransferResponse = {
            "transactionStatus":transfer_request.transaction_status,
            "paymentId":transfer_request.payment_id,
            "authId":transfer_request.auth_id
        }

        SepaCreditTransferDetailsResponse = {
            "transactionStatus":transfer_request.transaction_status,
            "paymentId":transfer_request.payment_id,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":transfer_request.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "SepaCreditTransferUpdateScaRequest": SepaCreditTransferUpdateScaRequest,
            "SepaCreditTransferResponse": SepaCreditTransferResponse,
            "SepaCreditTransferDetailsResponse": SepaCreditTransferDetailsResponse,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}


def deutsche_bank_transfer1(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        access_token = os.getenv("ACCESS_TOKEN")

        
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT"
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode":transfer_request.purpose_code,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":transfer_request.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}


def deutsche_bank_transfer(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # Si transfer_request es un UUID, buscar el objeto correspondiente
        if isinstance(transfer_request, uuid.UUID):
            transfer_request = SepaCreditTransferRequest.objects.filter(id=transfer_request).first()
            if not transfer_request:
                raise ValueError("No se encontró una transferencia con el ID proporcionado.")
            
            
        access_token = os.getenv("ACCESS_TOKEN")
        
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'            
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode": transfer_request.purpose_code,
            "requestedExecutionDate": transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_request.debtor_adress_zip_code_and_city,
                    "country": transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfer_request.debtor_account_iban,
                "bic": transfer_request.debtor_account_bic,
                "currency": transfer_request.debtor_account_currency
            },
            "creditor": {
                "name": transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_request.creditor_adress_zip_code_and_city,
                    "country": transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfer_request.creditor_account_iban,
                "bic": transfer_request.creditor_account_bic,
                "currency": transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfer_request.payment_identification_end_to_end_id),
                "instructionId": transfer_request.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount": str(transfer_request.instructed_amount),
                "currency": transfer_request.instructed_currency
            },
            "remittanceInformationStructured": transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured": transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}
    

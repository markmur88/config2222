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


def deutsche_bank_transfer(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # token_response = get_deutsche_bank_token()
        # access_token = token_response.get("access_token")
        
        # Si transfers es un UUID, buscar el objeto correspondiente
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("No se encontró una transferencia con el ID proporcionado.")
        else:
            # Validar que transfers no sea None
            if not transfers:
                raise ValueError("El objeto transfers no es válido.")
            
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': f"{psu_id}",
            'PSU-IP-Address': f"{psu_ip_address}"
        }

        # Construir los datos de la transferencia
        payload = {
            "paymentId":str(transfers.payment_id),
            "purposeCode":transfers.purpose_code,
            "requestedExecutionDate":transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.debtor_adress_zip_code_and_city,
                    "country":transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfers.debtor_account_iban,
                "bic":transfers.debtor_account_bic,
                "currency":transfers.debtor_account_currency
            },
            "creditor": {
                "name":transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.creditor_adress_zip_code_and_city,
                    "country":transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfers.creditor_account_iban,
                "bic":transfers.creditor_account_bic,
                "currency":transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfers.payment_identification_end_to_end_id),
                "instructionId":transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfers.instructed_amount),
                "currency":transfers.instructed_currency
            },
            "remittanceInformationStructured":transfers.remittance_information_structured,
            "remittanceInformationUnstructured":transfers.remittance_information_unstructured
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": payload,
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



def deutsche_bank_transfer0(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # token_response = get_deutsche_bank_token()
        # access_token = token_response.get("access_token")
        
        # Si transfers es un UUID, buscar el objeto correspondiente
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("No se encontró una transferencia con el ID proporcionado.")
        else:
            # Validar que transfers no sea None
            if not transfers:
                raise ValueError("El objeto transfers no es válido.")
            
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': f"{psu_id}",
            'PSU-IP-Address': f"{psu_ip_address}"
        }


        # Construir los datos de la transferencia
        payload = {
            "paymentId":str(transfers.payment_id),
            "purposeCode":transfers.purpose_code,
            "requestedExecutionDate":transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.debtor_adress_zip_code_and_city,
                    "country":transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfers.debtor_account_iban,
                "bic":transfers.debtor_account_bic,
                "currency":transfers.debtor_account_currency
            },
            "creditor": {
                "name":transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.creditor_adress_zip_code_and_city,
                    "country":transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfers.creditor_account_iban,
                "bic":transfers.creditor_account_bic,
                "currency":transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfers.payment_identification_end_to_end_id),
                "instructionId":transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfers.instructed_amount),
                "currency":transfers.instructed_currency
            },
            "remittanceInformationStructured":transfers.remittance_information_structured,
            "remittanceInformationUnstructured":transfers.remittance_information_unstructured
        }

        SepaCreditTransferUpdateScaRequest = {
            "action": "CREATE",
            "authId":transfers.auth_id,
        }

        SepaCreditTransferResponse = {
            "transactionStatus":transfers.transaction_status,
            "paymentId":transfers.payment_id,
            "authId":transfers.auth_id
        }

        SepaCreditTransferDetailsResponse = {
            "transactionStatus":transfers.transaction_status,
            "paymentId":transfers.payment_id,
            "requestedExecutionDate":transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.debtor_adress_zip_code_and_city,
                    "country":transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfers.debtor_account_iban,
                "bic":transfers.debtor_account_bic,
                "currency":transfers.debtor_account_currency
            },
            "creditor": {
                "name":transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.creditor_adress_zip_code_and_city,
                    "country":transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfers.creditor_account_iban,
                "bic":transfers.creditor_account_bic,
                "currency":transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfers.payment_identification_end_to_end_id),
                "instructionId":transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfers.instructed_amount),
                "currency":transfers.instructed_currency
            },
            "remittanceInformationStructured":transfers.remittance_information_structured,
            "remittanceInformationUnstructured":transfers.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": payload,
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


def deutsche_bank_transfer1(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': f"{psu_id}",
            'PSU-IP-Address': f"{psu_ip_address}"
        }


        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode":transfers.purpose_code,
            "requestedExecutionDate":transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.debtor_adress_zip_code_and_city,
                    "country":transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfers.debtor_account_iban,
                "bic":transfers.debtor_account_bic,
                "currency":transfers.debtor_account_currency
            },
            "creditor": {
                "name":transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfers.creditor_adress_zip_code_and_city,
                    "country":transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfers.creditor_account_iban,
                "bic":transfers.creditor_account_bic,
                "currency":transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfers.payment_identification_end_to_end_id),
                "instructionId":transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount":str(transfers.instructed_amount),
                "currency":transfers.instructed_currency
            },
            "remittanceInformationStructured":transfers.remittance_information_structured,
            "remittanceInformationUnstructured":transfers.remittance_information_unstructured
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


def deutsche_bank_transfer11(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # Si transfers es un UUID, buscar el objeto correspondiente
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("No se encontró una transferencia con el ID proporcionado.")
            
            
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': f"{psu_id}",
            'PSU-IP-Address': f"{psu_ip_address}"
        }


        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode": transfers.purpose_code,
            "requestedExecutionDate": transfers.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfers.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfers.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.debtor_adress_zip_code_and_city,
                    "country": transfers.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfers.debtor_account_iban,
                "bic": transfers.debtor_account_bic,
                "currency": transfers.debtor_account_currency
            },
            "creditor": {
                "name": transfers.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfers.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfers.creditor_adress_zip_code_and_city,
                    "country": transfers.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfers.creditor_account_iban,
                "bic": transfers.creditor_account_bic,
                "currency": transfers.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfers.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfers.payment_identification_end_to_end_id),
                "instructionId": transfers.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount": str(transfers.instructed_amount),
                "currency": transfers.instructed_currency
            },
            "remittanceInformationStructured": transfers.remittance_information_structured,
            "remittanceInformationUnstructured": transfers.remittance_information_unstructured
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
    

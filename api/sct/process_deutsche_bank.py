"""
Deutsche Bank integration module for SEPA Credit Transfers.

This module handles the communication with Deutsche Bank's API for processing
SEPA Credit Transfers, including formatting requests and handling responses.
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Union, Optional

import requests
from django.conf import settings
from dotenv import load_dotenv

from api.sct.models import SepaCreditTransferRequest

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Constants
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def deutsche_bank_transfer(idempotency_key: str, transfers: Union[SepaCreditTransferRequest, uuid.UUID]) -> Dict[str, Any]:
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This is the main function for Deutsche Bank transfers.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: Either a SepaCreditTransferRequest object or a UUID to look it up
        
    Returns:
        dict: Response containing success information or error details
    """
    try:
        # If transfers is a UUID, look up the corresponding object
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("Transfer with the provided ID not found.")
        else:
            # Validate that transfers is not None
            if not transfers:
                raise ValueError("The transfers object is not valid.")
                
        access_token = os.getenv("ACCESS_TOKEN")
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'
        }
        
        # Build transfer data
        payload = {
            "paymentId": str(transfers.payment_id),
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
        
        # Send request to bank
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": payload,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer0(idempotency_key: str, transfers: Union[SepaCreditTransferRequest, uuid.UUID]) -> Dict[str, Any]:
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This version returns all related response objects for testing.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: Either a SepaCreditTransferRequest object or a UUID to look it up
        
    Returns:
        dict: Response containing all related objects or error details
    """
    try:
        # If transfers is a UUID, look up the corresponding object
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("Transfer with the provided ID not found.")
        else:
            # Validate that transfers is not None
            if not transfers:
                raise ValueError("The transfers object is not valid.")
                
        access_token = os.getenv("ACCESS_TOKEN")
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT",
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'
        }
        
        # Build transfer data
        payload = {
            "paymentId": str(transfers.payment_id),
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
        
        SepaCreditTransferUpdateScaRequest = {
            "action": "CREATE",
            "authId": transfers.auth_id,
        }
        
        SepaCreditTransferResponse = {
            "transactionStatus": transfers.transaction_status,
            "paymentId": transfers.payment_id,
            "authId": transfers.auth_id
        }
        
        SepaCreditTransferDetailsResponse = {
            "transactionStatus": transfers.transaction_status,
            "paymentId": transfers.payment_id,
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
        
        # Send request to bank
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": payload,
            "SepaCreditTransferUpdateScaRequest": SepaCreditTransferUpdateScaRequest,
            "SepaCreditTransferResponse": SepaCreditTransferResponse,
            "SepaCreditTransferDetailsResponse": SepaCreditTransferDetailsResponse,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer1(idempotency_key: str, transfers: SepaCreditTransferRequest) -> Dict[str, Any]:
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This version uses a simplified request format.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: SepaCreditTransferRequest object with transfer details
        
    Returns:
        dict: Response containing success information or error details
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
        
        # Build transfer data
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
        
        # Send request to bank
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer11(idempotency_key: str, transfers: Union[SepaCreditTransferRequest, uuid.UUID]) -> Dict[str, Any]:
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This version includes additional headers for authentication.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: Either a SepaCreditTransferRequest object or a UUID to look it up
        
    Returns:
        dict: Response containing success information or error details
    """
    try:
        # If transfers is a UUID, look up the corresponding object
        if isinstance(transfers, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers).first()
            if not transfers:
                raise ValueError("Transfer with the provided ID not found.")
                
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
        
        # Build transfer data
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
        
        # Send request to bank
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}
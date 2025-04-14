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

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Constants
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def mock_bank_response(transfer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a mock bank response for development/testing.
    
    Args:
        transfer_data: The transfer request data
        
    Returns:
        Dict[str, Any]: Mock response data
    """
    return {
        "SepaCreditTransferRequest": transfer_data,
        "bank_response": {
            "transactionStatus": "ACCP",
            "paymentId": str(uuid.uuid4()),
            "authId": "mock-auth-id"
        }
    }


def deutsche_bank_transfer(idempotency_key: str, transfers_param):
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This is the main function for Deutsche Bank transfers.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers_param: Either a SepaCreditTransferRequest object or a UUID to look it up
        
    Returns:
        dict: Response containing success information or error details
    """
    # Import here to avoid naming conflicts
    from api.sct.models import SepaCreditTransferRequest
    
    try:
        # Determine what was passed in and get the transfer object
        if isinstance(transfers_param, uuid.UUID):
            # If it's a UUID, look up the transfer
            transfer_obj = SepaCreditTransferRequest.objects.filter(id=transfers_param).first()
            if not transfer_obj:
                return {"error": f"Transfer with ID {transfers_param} not found."}
        else:
            # Otherwise, assume it's already a transfer object
            transfer_obj = transfers_param
            if not transfer_obj:
                return {"error": "The transfer object is not valid."}
        
        # Build transfer data
        payload = {
            "paymentId": str(transfer_obj.payment_id),
            "purposeCode": transfer_obj.purpose_code,
            "requestedExecutionDate": transfer_obj.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfer_obj.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfer_obj.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_obj.debtor_adress_zip_code_and_city,
                    "country": transfer_obj.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfer_obj.debtor_account_iban,
                "bic": transfer_obj.debtor_account_bic,
                "currency": transfer_obj.debtor_account_currency
            },
            "creditor": {
                "name": transfer_obj.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfer_obj.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_obj.creditor_adress_zip_code_and_city,
                    "country": transfer_obj.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfer_obj.creditor_account_iban,
                "bic": transfer_obj.creditor_account_bic,
                "currency": transfer_obj.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfer_obj.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfer_obj.payment_identification_end_to_end_id),
                "instructionId": transfer_obj.payment_identification_instruction_id
            },
            "instructedAmount": {
                "amount": str(transfer_obj.instructed_amount),
                "currency": transfer_obj.instructed_currency
            },
            "remittanceInformationStructured": transfer_obj.remittance_information_structured,
            "remittanceInformationUnstructured": transfer_obj.remittance_information_unstructured
        }
        
        # For development/testing, skip the actual API call
        if settings.DEBUG:
            logger.info("DEBUG mode: Using mock Deutsche Bank response")
            return mock_bank_response(payload)
        
        # Now use transfer_obj for the rest of the function
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
        
        # Send request to bank
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": payload,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        response_text = getattr(e.response, 'text', 'No response text available')
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response_text}")
        return {"error": f"HTTPError: {response_text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer0(idempotency_key: str, transfers_param):
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This version returns all related response objects for testing.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers_param: Either a SepaCreditTransferRequest object or a UUID to look it up
        
    Returns:
        dict: Response containing all related objects or error details
    """
    # Import here to avoid naming conflicts
    from api.sct.models import SepaCreditTransferRequest
    
    try:
        # Determine what was passed in and get the transfer object
        if isinstance(transfers_param, uuid.UUID):
            # If it's a UUID, look up the transfer
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers_param).first()
            if not transfers:
                return {"error": f"Transfer with ID {transfers_param} not found."}
        else:
            # Otherwise, assume it's already a transfer object
            transfers = transfers_param
            if not transfers:
                return {"error": "The transfer object is not valid."}
        
        # For development/testing, use mock data
        if settings.DEBUG:
            logger.info("DEBUG mode: Using mock Deutsche Bank response")
            # Create mock response objects
            payload = {
                "paymentId": str(transfers.payment_id),
                "purposeCode": transfers.purpose_code,
                "requestedExecutionDate": transfers.requested_execution_date.strftime("%Y-%m-%d"),
                # Rest of the payload fields...
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
                # Rest of the response fields...
            }
            
            return {
                "SepaCreditTransferRequest": payload,
                "SepaCreditTransferUpdateScaRequest": SepaCreditTransferUpdateScaRequest,
                "SepaCreditTransferResponse": SepaCreditTransferResponse,
                "SepaCreditTransferDetailsResponse": SepaCreditTransferDetailsResponse,
                "bank_response": {"mock": "response"}
            }
            
        # Real implementation for production
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
        response_text = getattr(e.response, 'text', 'No response text available')
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response_text}")
        return {"error": f"HTTPError: {response_text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer1(idempotency_key: str, transfers_param):
    """
    Process a bank transfer using SepaCreditTransferRequest data with Deutsche Bank.
    
    This version uses a simplified request format.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers_param: SepaCreditTransferRequest object with transfer details
        
    Returns:
        dict: Response containing success information or error details
    """
    # Import here to avoid naming conflicts
    from api.sct.models import SepaCreditTransferRequest
    
    try:
        # Make sure transfers_param is a SepaCreditTransferRequest object
        if isinstance(transfers_param, uuid.UUID):
            transfers = SepaCreditTransferRequest.objects.filter(id=transfers_param).first()
            if not transfers:
                return {"error": f"Transfer with ID {transfers_param} not found."}
        else:
            transfers = transfers_param
        
        # For development/testing, use mock data
        if settings.DEBUG:
            logger.info("DEBUG mode: Using mock Deutsche Bank response")
            # Build payload
            payload = {
                "purposeCode": transfers.purpose_code,
                "requestedExecutionDate": transfers.requested_execution_date.strftime("%Y-%m-%d"),
                # Rest of the payload fields...
            }
            
            return mock_bank_response(payload)
            
        # Continue with real implementation for production
        access_token = os.getenv("ACCESS_TOKEN")
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT"
        }
        
        # Build transfer data
        payload = {
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
        response_text = getattr(e.response, 'text', 'No response text available')
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response_text}")
        return {"error": f"HTTPError: {response_text}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


# Note: The duplicate function definition was removed as it was causing conflicts
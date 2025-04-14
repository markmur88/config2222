"""
Deutsche Bank utility functions.

This module contains utility functions for working with Deutsche Bank's API,
separate from the main processing module to avoid naming conflicts.
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union

import requests
from django.conf import settings
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def mock_deutsche_bank_transfer(transfer_data: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
    """
    Create a mock Deutsche Bank transfer response for development.
    
    Args:
        transfer_data: Data for the transfer
        idempotency_key: Unique key to ensure idempotency
        
    Returns:
        dict: Mock response data
    """
    logger.info("Using mock Deutsche Bank transfer response")
    
    # Create a mock successful response
    return {
        "SepaCreditTransferRequest": transfer_data,
        "bank_response": {
            "transactionStatus": "ACCP",
            "paymentId": str(uuid.uuid4()),
            "authId": str(uuid.uuid4())
        }
    }


def process_bank_transfer(transfer_obj, idempotency_key: str) -> Dict[str, Any]:
    """
    Process a bank transfer with Deutsche Bank.
    
    Args:
        transfer_obj: The transfer object with all necessary data
        idempotency_key: Unique key to ensure idempotency
        
    Returns:
        dict: Response containing success information or error details
    """
    try:
        # Check if transfer_obj is valid
        if not transfer_obj:
            return {"error": "Invalid transfer object"}
            
        # Return mock data in DEBUG mode
        if settings.DEBUG:
            return mock_deutsche_bank_transfer(
                build_transfer_payload(transfer_obj),
                idempotency_key
            )
            
        # Continue with real implementation for production
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
        payload = build_transfer_payload(transfer_obj)
        
        # Send request to bank
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Return organized responses
        return {
            "SepaCreditTransferRequest": payload,
            "bank_response": response.json()
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {"error": f"HTTPError: {str(e)}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def build_transfer_payload(transfer_obj) -> Dict[str, Any]:
    """
    Build the payload for a Deutsche Bank transfer request.
    
    Args:
        transfer_obj: The transfer object with all necessary data
        
    Returns:
        dict: The formatted payload
    """
    return {
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
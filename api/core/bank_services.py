"""
Bank transfer services for external bank APIs.

This module provides utility functions for performing banking operations
such as transfers through different bank APIs.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import requests
from django.conf import settings
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from api.core.auth_services import get_deutsche_bank_token, get_memo_bank_token


# Configure logger
logger = logging.getLogger("bank_services")


def memo_bank_transfer(
    source_account: str,
    destination_account: str,
    amount: float,
    currency: str,
    idempotency_key: str
) -> Dict[str, Any]:
    """
    Execute a transfer via Memo Bank API.
    
    Args:
        source_account: The source account number
        destination_account: The destination account number
        amount: The amount to transfer
        currency: The currency code (e.g., EUR, USD)
        idempotency_key: Unique key to prevent duplicate transfers
        
    Returns:
        Dict[str, Any]: API response or error information
    """
    try:
        # Get access token
        token_response = get_memo_bank_token()
        if "error" in token_response:
            logger.error(f"Failed to get token for Memo Bank: {token_response['error']}")
            return {"error": "Authentication failed with Memo Bank"}
        
        access_token = token_response.get("access_token")
        
        # Prepare API request
        url = f"{settings.MEMO_BANK_API_URL}/transfers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        
        payload = {
            "source_account": source_account,
            "destination_account": destination_account,
            "amount": str(amount),
            "currency": currency,
            "transfer_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Execute transfer
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise error for non-2xx status codes
        
        logger.info(f"Memo Bank transfer successful: {idempotency_key}")
        return response.json()
    
    except HTTPError as e:
        logger.error(f"HTTP Error with Memo Bank: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {"error": f"Error with Memo Bank API: {str(e)}"}
    
    except Timeout:
        logger.error("Timeout connecting to Memo Bank")
        return {"error": "Connection to Memo Bank timed out"}
    
    except ConnectionError:
        logger.error("Connection error with Memo Bank")
        return {"error": "Could not connect to Memo Bank"}
    
    except RequestException as e:
        logger.error(f"Request error with Memo Bank: {e}")
        return {"error": f"Request failed: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error with Memo Bank transfer: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def deutsche_bank_transfer(
    idempotency_key: str,
    sender_name: str,
    sender_iban: str,
    sender_bic: str,
    recipient_name: str,
    recipient_iban: str,
    recipient_bic: str,
    status: str,
    amount: float,
    currency: str,
    execution_date: str
) -> Dict[str, Any]:
    """
    Execute a transfer via Deutsche Bank API.
    
    Args:
        idempotency_key: Unique key to prevent duplicate transfers
        sender_name: Name of the sending account holder
        sender_iban: IBAN of the sending account
        sender_bic: BIC of the sending bank
        recipient_name: Name of the receiving account holder
        recipient_iban: IBAN of the receiving account
        recipient_bic: BIC of the receiving bank
        status: Status of the transfer (e.g., "PDNG", "ACCP")
        amount: The amount to transfer
        currency: The currency code (e.g., EUR, USD)
        execution_date: The date to execute the transfer (YYYY-MM-DD)
        
    Returns:
        Dict[str, Any]: API response or error information
    """
    try:
        # Get access token
        token_response = get_deutsche_bank_token()
        if "error" in token_response:
            logger.error(f"Failed to get token for Deutsche Bank: {token_response['error']}")
            return {"error": "Authentication failed with Deutsche Bank"}
        
        access_token = token_response.get("access_token")
        
        # Prepare API request
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        
        payload = {
            "sender_name": sender_name,
            "sender_iban": sender_iban,
            "sender_bic": sender_bic,
            "recipient_name": recipient_name,
            "recipient_iban": recipient_iban,
            "recipient_bic": recipient_bic,
            "amount": str(amount),
            "currency": currency,
            "status": status,
            "execution_date": execution_date
        }
        
        # Execute transfer
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise error for non-2xx status codes
        
        logger.info(f"Deutsche Bank transfer successful: {idempotency_key}")
        return response.json()
    
    except HTTPError as e:
        logger.error(f"HTTP Error with Deutsche Bank: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {"error": f"Error with Deutsche Bank API: {str(e)}"}
    
    except Timeout:
        logger.error("Timeout connecting to Deutsche Bank")
        return {"error": "Connection to Deutsche Bank timed out"}
    
    except ConnectionError:
        logger.error("Connection error with Deutsche Bank")
        return {"error": "Could not connect to Deutsche Bank"}
    
    except RequestException as e:
        logger.error(f"Request error with Deutsche Bank: {e}")
        return {"error": f"Request failed: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error with Deutsche Bank transfer: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def sepa_transfer(
    idempotency_key: str,
    sender_name: str,
    sender_iban: str,
    sender_bic: str,
    recipient_name: str,
    recipient_iban: str,
    recipient_bic: str,
    status: str,
    amount: float,
    currency: str,
    execution_date: str,
    reference: Optional[str] = None,
    purpose_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a SEPA transfer via the bank API.
    
    Args:
        idempotency_key: Unique key to prevent duplicate transfers
        sender_name: Name of the sending account holder
        sender_iban: IBAN of the sending account
        sender_bic: BIC of the sending bank
        recipient_name: Name of the receiving account holder
        recipient_iban: IBAN of the receiving account
        recipient_bic: BIC of the receiving bank
        status: Status of the transfer (e.g., "PDNG", "ACCP")
        amount: The amount to transfer
        currency: The currency code (e.g., EUR)
        execution_date: The date to execute the transfer (YYYY-MM-DD)
        reference: Optional reference information
        purpose_code: Optional SEPA purpose code
        
    Returns:
        Dict[str, Any]: API response or error information
    """
    try:
        # Get access token
        token_response = get_deutsche_bank_token()
        if "error" in token_response:
            logger.error(f"Failed to get token for SEPA transfer: {token_response['error']}")
            return {"error": "Authentication failed for SEPA transfer"}
        
        access_token = token_response.get("access_token")
        
        # Prepare API request
        url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        
        payload = {
            "sender_name": sender_name,
            "sender_iban": sender_iban,
            "sender_bic": sender_bic,
            "recipient_name": recipient_name,
            "recipient_iban": recipient_iban,
            "recipient_bic": recipient_bic,
            "amount": str(amount),
            "currency": currency,
            "status": status,
            "execution_date": execution_date,
            "transfer_type": "SEPA"
        }
        
        # Add optional fields if provided
        if reference:
            payload["reference"] = reference
        if purpose_code:
            payload["purpose_code"] = purpose_code
        
        # Execute transfer
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise error for non-2xx status codes
        
        logger.info(f"SEPA transfer successful: {idempotency_key}")
        return response.json()
    
    except HTTPError as e:
        logger.error(f"HTTP Error with SEPA transfer: {e}, Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return {"error": f"Error with SEPA transfer API: {str(e)}"}
    
    except Timeout:
        logger.error("Timeout connecting to SEPA transfer service")
        return {"error": "Connection to SEPA transfer service timed out"}
    
    except ConnectionError:
        logger.error("Connection error with SEPA transfer service")
        return {"error": "Could not connect to SEPA transfer service"}
    
    except RequestException as e:
        logger.error(f"Request error with SEPA transfer: {e}")
        return {"error": f"Request failed: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error with SEPA transfer: {e}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def check_transfer_status(
    transfer_id: str,
    bank_type: str = "deutsche"
) -> Dict[str, Any]:
    """
    Check the status of a previously submitted transfer.
    
    Args:
        transfer_id: The ID of the transfer to check
        bank_type: The type of bank ("memo" or "deutsche")
        
    Returns:
        Dict[str, Any]: Transfer status information
    """
    try:
        # Get appropriate token based on bank type
        if bank_type.lower() == "memo":
            token_response = get_memo_bank_token()
            url = f"{settings.MEMO_BANK_API_URL}/transfers/{transfer_id}"
        else:  # deutsche
            token_response = get_deutsche_bank_token()
            url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers/{transfer_id}"
        
        if "error" in token_response:
            logger.error(f"Failed to get token for status check: {token_response['error']}")
            return {"error": "Authentication failed for status check"}
        
        access_token = token_response.get("access_token")
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get transfer status
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Transfer status check successful: {transfer_id}")
        return response.json()
    
    except Exception as e:
        logger.error(f"Error checking transfer status: {e}", exc_info=True)
        return {"error": f"Error checking transfer status: {str(e)}"}
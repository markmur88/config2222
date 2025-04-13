"""
Authentication services for external bank APIs.

This module provides utility functions for obtaining authentication tokens
from different banking APIs for use in API calls.
"""
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logger
logger = logging.getLogger(__name__)


def get_memo_bank_token() -> Dict[str, Any]:
    """
    Obtain an OAuth token from Memo Bank API.
    
    Returns:
        Dict[str, Any]: Dictionary containing access token or error information
        
    Raises:
        RequestException: If there's an issue with the request
    """
    try:
        url = f"{settings.MEMO_BANK_API_URL}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.MEMO_BANK_CLIENT_ID,
            "client_secret": settings.MEMO_BANK_CLIENT_SECRET
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Successfully obtained Memo Bank token")
            return token_data
        else:
            error_msg = f"Failed to obtain Memo Bank token: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    except Timeout:
        error_msg = "Timeout while connecting to Memo Bank API"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except ConnectionError:
        error_msg = "Connection error while connecting to Memo Bank API"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except RequestException as e:
        error_msg = f"Request exception while obtaining Memo Bank token: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error while obtaining Memo Bank token: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


def get_deutsche_bank_token() -> Dict[str, Any]:
    """
    Obtain an OAuth token from Deutsche Bank API.
    
    Returns:
        Dict[str, Any]: Dictionary containing access token or error information
        
    Raises:
        RequestException: If there's an issue with the request
    """
    try:
        url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.DEUTSCHE_BANK_CLIENT_ID,
            "client_secret": settings.DEUTSCHE_BANK_CLIENT_SECRET
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Successfully obtained Deutsche Bank token")
            return token_data
        else:
            error_msg = f"Failed to obtain Deutsche Bank token: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    except Timeout:
        error_msg = "Timeout while connecting to Deutsche Bank API"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except ConnectionError:
        error_msg = "Connection error while connecting to Deutsche Bank API"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except RequestException as e:
        error_msg = f"Request exception while obtaining Deutsche Bank token: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error while obtaining Deutsche Bank token: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


def verify_token(token: str, bank_type: str = "deutsche") -> Dict[str, Any]:
    """
    Verify if a token is valid and not expired.
    
    Args:
        token: The token to verify
        bank_type: The type of bank ("memo" or "deutsche")
        
    Returns:
        Dict[str, Any]: Token verification result
    """
    try:
        if bank_type.lower() == "memo":
            url = f"{settings.MEMO_BANK_API_URL}/oauth/verify"
        else:  # deutsche
            url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/verify"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Token verification successful for {bank_type} bank")
            return {"valid": True, "data": response.json()}
        else:
            error_msg = f"Token verification failed for {bank_type} bank: {response.status_code} - {response.text}"
            logger.warning(error_msg)
            return {"valid": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Error verifying token for {bank_type} bank: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"valid": False, "error": error_msg}


def refresh_token(refresh_token: str, bank_type: str = "deutsche") -> Dict[str, Any]:
    """
    Refresh an existing OAuth token.
    
    Args:
        refresh_token: The refresh token to use
        bank_type: The type of bank ("memo" or "deutsche")
        
    Returns:
        Dict[str, Any]: New token information or error
    """
    try:
        if bank_type.lower() == "memo":
            url = f"{settings.MEMO_BANK_API_URL}/oauth/token"
            client_id = settings.MEMO_BANK_CLIENT_ID
            client_secret = settings.MEMO_BANK_CLIENT_SECRET
        else:  # deutsche
            url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/token"
            client_id = settings.DEUTSCHE_BANK_CLIENT_ID
            client_secret = settings.DEUTSCHE_BANK_CLIENT_SECRET
        
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            logger.info(f"Successfully refreshed {bank_type} bank token")
            return token_data
        else:
            error_msg = f"Failed to refresh {bank_type} bank token: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"Error refreshing {bank_type} bank token: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}
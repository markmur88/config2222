"""
Utility functions for API integrations and common operations.

This module provides helper functions for making API requests to various
banking services and performing other utility operations.
"""
import logging
from typing import Dict, Any, Optional, List, Union

import requests
from django.conf import settings
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logger
logger = logging.getLogger(__name__)


def make_api_request(
    url: str, 
    method: str = 'GET', 
    payload: Optional[Dict[str, Any]] = None, 
    headers: Optional[Dict[str, str]] = None, 
    params: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an API request with error handling and logging.
    
    A generic function for making HTTP requests to external APIs
    with consistent error handling.
    
    Args:
        url: The API endpoint URL
        method: The HTTP method (GET, POST, PUT, DELETE)
        payload: The request body for POST/PUT requests
        headers: HTTP headers to include
        params: URL parameters
        timeout: Request timeout in seconds
        
    Returns:
        Dict[str, Any]: The API response or error information
    """
    try:
        headers = headers or {}
        
        # Set default content type if not provided
        if 'Content-Type' not in headers and method in ['POST', 'PUT', 'PATCH']:
            headers['Content-Type'] = 'application/json'
        
        # Make the request based on the method
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=payload, headers=headers, params=params, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=payload, headers=headers, params=params, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=timeout)
        elif method == 'PATCH':
            response = requests.patch(url, json=payload, headers=headers, params=params, timeout=timeout)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}
        
        # Raise exception for error status codes
        response.raise_for_status()
        
        # Return JSON response if successful and response has content
        if response.status_code == 204 or not response.content:
            return {"success": True, "status_code": response.status_code}
        
        return response.json()
    
    except Timeout:
        error_msg = f"Request to {url} timed out after {timeout} seconds"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except ConnectionError:
        error_msg = f"Connection error when connecting to {url}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


def memo_bank_request(
    endpoint: str, 
    payload: Dict[str, Any], 
    headers: Optional[Dict[str, str]] = None,
    method: str = 'POST'
) -> Dict[str, Any]:
    """
    Make a request to the Memo Bank API.
    
    Args:
        endpoint: The API endpoint (without base URL)
        payload: The request body
        headers: Additional HTTP headers
        method: The HTTP method (default: POST)
        
    Returns:
        Dict[str, Any]: The API response or error information
    """
    url = f"{settings.MEMO_BANK_API_URL}/{endpoint.lstrip('/')}"
    
    # Prepare headers
    request_headers = headers or {}
    request_headers.update({
        "Authorization": f"Bearer {settings.MEMO_BANK_CLIENT_SECRET}",
        "Content-Type": "application/json"
    })
    
    logger.info(f"Making {method} request to Memo Bank: {endpoint}")
    return make_api_request(url, method, payload, request_headers)


def deutsche_bank_request(
    endpoint: str, 
    payload: Dict[str, Any], 
    headers: Optional[Dict[str, str]] = None,
    method: str = 'POST'
) -> Dict[str, Any]:
    """
    Make a request to the Deutsche Bank API.
    
    Args:
        endpoint: The API endpoint (without base URL)
        payload: The request body
        headers: Additional HTTP headers
        method: The HTTP method (default: POST)
        
    Returns:
        Dict[str, Any]: The API response or error information
    """
    url = f"{settings.DEUTSCHE_BANK_API_URL}/{endpoint.lstrip('/')}"
    
    # Prepare headers
    request_headers = headers or {}
    request_headers.update({
        "Authorization": f"Bearer {settings.DEUTSCHE_BANK_CLIENT_SECRET}",
        "Content-Type": "application/json"
    })
    
    logger.info(f"Making {method} request to Deutsche Bank: {endpoint}")
    return make_api_request(url, method, payload, request_headers)


def get_memo_bank_accounts(token: str) -> Dict[str, Any]:
    """
    Get a list of accounts from Memo Bank.
    
    Args:
        token: The authentication token
        
    Returns:
        Dict[str, Any]: List of accounts or error information
    """
    url = f"{settings.MEMO_BANK_API_URL}/accounts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    logger.info("Fetching accounts from Memo Bank")
    return make_api_request(url, 'GET', headers=headers)


def get_deutsche_bank_accounts(token: str) -> Dict[str, Any]:
    """
    Get a list of accounts from Deutsche Bank.
    
    Args:
        token: The authentication token
        
    Returns:
        Dict[str, Any]: List of accounts or error information
    """
    url = f"{settings.DEUTSCHE_BANK_API_URL}/accounts"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    logger.info("Fetching accounts from Deutsche Bank")
    return make_api_request(url, 'GET', headers=headers)


def format_iban(iban: str) -> str:
    """
    Format an IBAN for display with proper spacing.
    
    Args:
        iban: The raw IBAN string
        
    Returns:
        str: The formatted IBAN
    """
    # Remove any existing spaces and convert to uppercase
    iban = iban.replace(' ', '').upper()
    
    # Format with a space every 4 characters
    return ' '.join(iban[i:i+4] for i in range(0, len(iban), 4))


def mask_iban(iban: str) -> str:
    """
    Mask an IBAN for display while preserving some digits for identification.
    
    Args:
        iban: The raw IBAN string
        
    Returns:
        str: The masked IBAN
    """
    # Remove any existing spaces
    iban = iban.replace(' ', '')
    
    # Keep country code and check digits, mask the rest except last 4 digits
    country_code = iban[:2]
    check_digits = iban[2:4]
    masked_part = '*' * (len(iban) - 8)
    last_digits = iban[-4:]
    
    return f"{country_code}{check_digits} {masked_part} {last_digits}"


def normalize_bic(bic: str) -> str:
    """
    Normalize a BIC by removing spaces and ensuring proper format.
    
    Args:
        bic: The BIC to normalize
        
    Returns:
        str: The normalized BIC
    """
    # Remove any spaces and convert to uppercase
    return bic.replace(' ', '').upper()
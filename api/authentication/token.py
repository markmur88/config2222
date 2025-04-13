"""
Token management utilities for API authentication.

This module provides functions for working with authentication tokens,
including retrieving and refreshing tokens from the authentication server.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional, Tuple

from django.conf import settings
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get tokens from environment variables
ACCESS_TOKEN = {
    "refresh": os.getenv("REFRESH_TOKEN"),
    "access": os.getenv("ACCESS_TOKEN"),
}


def get_access_token(refresh_token: str) -> Optional[str]:
    """
    Get a new access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to use
        
    Returns:
        Optional[str]: The new access token or None if request fails
        
    Raises:
        Exception: If the token refresh request fails
    """
    try:
        token_url = getattr(settings, 'TOKEN_REFRESH_URL', 'http://127.0.0.1:8000/api/auth/token/refresh/')
        response = requests.post(
            token_url, 
            data={"refresh": refresh_token},
            timeout=10  # Add timeout for safety
        )
        
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        return response.json().get("access")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error refreshing token: {e}", exc_info=True)
        raise Exception(f"Error refreshing token: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in token refresh: {e}", exc_info=True)
        raise Exception(f"Unexpected error in token refresh: {str(e)}")


def refresh_all_tokens() -> Dict[str, str]:
    """
    Refresh both access and refresh tokens.
    
    Returns:
        Dict[str, str]: Dictionary containing new access and refresh tokens
        
    Raises:
        Exception: If the token refresh request fails
    """
    try:
        token_url = getattr(settings, 'TOKEN_REFRESH_URL', 'http://127.0.0.1:8000/api/auth/token/refresh/')
        response = requests.post(
            token_url, 
            data={"refresh": ACCESS_TOKEN["refresh"]},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Update the global token dictionary
        ACCESS_TOKEN["access"] = data.get("access")
        ACCESS_TOKEN["refresh"] = data.get("refresh")
        
        return {
            "access": data.get("access"),
            "refresh": data.get("refresh")
        }
    
    except Exception as e:
        logger.error(f"Error refreshing tokens: {e}", exc_info=True)
        raise Exception(f"Error refreshing tokens: {str(e)}")


def validate_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a token by making a request to the validation endpoint.
    
    Args:
        token: The token to validate
        
    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: A tuple containing:
            - A boolean indicating if the token is valid
            - The token payload if valid, None otherwise
    """
    try:
        # Use verify token endpoint
        token_url = getattr(settings, 'TOKEN_VERIFY_URL', 'http://127.0.0.1:8000/api/auth/token/verify/')
        response = requests.post(
            token_url, 
            data={"token": token},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, response.json()
        return False, None
    
    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        return False, None


def get_authenticated_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Get headers for an authenticated request.
    
    Args:
        token: The access token to use (uses stored token if None)
        
    Returns:
        Dict[str, str]: Headers dictionary with Authorization
    """
    access_token = token or ACCESS_TOKEN.get("access")
    if not access_token:
        # Try to refresh the token if we don't have one
        access_token = get_access_token(ACCESS_TOKEN.get("refresh", ""))
    
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


# Remove the test code that was directly in the module
# and replace with a function that can be called when needed
def test_token_refresh():
    """
    Test the token refresh functionality.
    
    Returns:
        str: The new access token
    """
    try:
        access_token = get_access_token(ACCESS_TOKEN["refresh"])
        logger.info(f"New access token obtained successfully")
        return access_token
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
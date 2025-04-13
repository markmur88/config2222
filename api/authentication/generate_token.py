"""
Token generation utilities for API authentication.

This module provides functions for generating secure JWT tokens
using RSA private keys for authentication with API endpoints.
"""
import jwt
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

from django.conf import settings


logger = logging.getLogger(__name__)


def generate_token(user_id: Union[int, str], expiry_hours: int = 1) -> Optional[str]:
    """
    Generate a JWT token for a user using RSA signing.
    
    Args:
        user_id: The ID of the user for whom to generate the token
        expiry_hours: Number of hours until the token expires (default: 1)
        
    Returns:
        Optional[str]: The generated JWT token or None if token generation fails
        
    Raises:
        ValueError: If private key file is missing or invalid
    """
    try:
        # Get private key path from settings or use default
        private_key_path = getattr(settings, 'JWT_PRIVATE_KEY_PATH', '/private.pem')
        
        # Ensure the private key file exists
        if not os.path.exists(private_key_path):
            raise ValueError(f"Private key file not found at: {private_key_path}")
        
        # Read the private key
        with open(private_key_path, 'r') as f:
            private_key = f.read()
        
        # Create the token payload
        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        # Generate and return the token
        token = jwt.encode(payload, private_key, algorithm='RS256')
        return token
    
    except FileNotFoundError:
        logger.error(f"Private key file not found at: {private_key_path}")
        raise ValueError(f"Private key file not found at: {private_key_path}")
    
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}", exc_info=True)
        return None


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a JWT token and extract its payload.
    
    Args:
        token: The JWT token to validate
        
    Returns:
        Dict[str, Any]: The token payload if valid
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid
        jwt.ExpiredSignatureError: If the token has expired
        ValueError: If public key file is missing
    """
    # Get public key path from settings or use default
    public_key_path = getattr(settings, 'JWT_PUBLIC_KEY_PATH', '/public.pem')
    
    # Ensure the public key file exists
    if not os.path.exists(public_key_path):
        raise ValueError(f"Public key file not found at: {public_key_path}")
    
    # Read the public key
    with open(public_key_path, 'r') as f:
        public_key = f.read()
    
    # Decode and verify the token
    payload = jwt.decode(token, public_key, algorithms=['RS256'])
    return payload


def generate_refresh_token(user_id: Union[int, str], expiry_days: int = 7) -> Optional[str]:
    """
    Generate a longer-lived refresh token for a user.
    
    Args:
        user_id: The ID of the user for whom to generate the token
        expiry_days: Number of days until the token expires (default: 7)
        
    Returns:
        Optional[str]: The generated refresh token or None if token generation fails
    """
    try:
        # Convert days to hours for the generate_token function
        expiry_hours = expiry_days * 24
        
        # Create a token with refresh type
        refresh_token = generate_token(user_id, expiry_hours)
        return refresh_token
    
    except Exception as e:
        logger.error(f"Error generating refresh token: {str(e)}", exc_info=True)
        return None


def generate_token_pair(user_id: Union[int, str]) -> Dict[str, str]:
    """
    Generate both access and refresh tokens for a user.
    
    Args:
        user_id: The ID of the user for whom to generate the tokens
        
    Returns:
        Dict[str, str]: Dictionary containing both tokens
    """
    access_token = generate_token(user_id)
    refresh_token = generate_refresh_token(user_id)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer'
    }
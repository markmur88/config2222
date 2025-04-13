"""
JWT token generation and validation for authentication.

This module provides utilities for generating and validating JWT tokens
used for user authentication in the API.
"""
import datetime
from typing import Dict, Any, Optional, Tuple, Union

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_access_token(user_id: Union[int, str], expires_in: int = None) -> str:
    """
    Generate a JWT access token for a user.
    
    Args:
        user_id: The ID of the user for whom to generate the token
        expires_in: Token expiry time in seconds (default: from settings)
        
    Returns:
        str: The generated JWT token
        
    Raises:
        ValueError: If user_id is invalid
    """
    if not user_id:
        raise ValueError("User ID is required to generate an access token")
    
    # Get expiry time from settings if not provided
    if expires_in is None:
        expires_in = getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', 3600)  # Default: 1 hour
    
    # Set token payload
    payload = {
        'user_id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        'iat': datetime.datetime.utcnow(),
        'token_type': 'access'
    }
    
    # Generate token
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
    )
    
    return token


def generate_refresh_token(user_id: Union[int, str], expires_in: int = None) -> str:
    """
    Generate a JWT refresh token for a user.
    
    Args:
        user_id: The ID of the user for whom to generate the token
        expires_in: Token expiry time in seconds (default: from settings)
        
    Returns:
        str: The generated JWT refresh token
        
    Raises:
        ValueError: If user_id is invalid
    """
    if not user_id:
        raise ValueError("User ID is required to generate a refresh token")
    
    # Get expiry time from settings if not provided
    if expires_in is None:
        expires_in = getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', 604800)  # Default: 7 days
    
    # Set token payload
    payload = {
        'user_id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
        'iat': datetime.datetime.utcnow(),
        'token_type': 'refresh'
    }
    
    # Generate token
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
    )
    
    return token


def generate_token_response(user_id: Union[int, str]) -> Dict[str, Any]:
    """
    Generate both access and refresh tokens for a user.
    
    Args:
        user_id: The ID of the user for whom to generate the tokens
        
    Returns:
        Dict[str, Any]: Dictionary containing both tokens and their expiry times
    """
    access_token = generate_access_token(user_id)
    refresh_token = generate_refresh_token(user_id)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer'
    }


def validate_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a JWT token and extract its payload.
    
    Args:
        token: The JWT token to validate
        
    Returns:
        Tuple containing:
        - bool: Whether the token is valid
        - Optional[Dict[str, Any]]: The token payload if valid, None otherwise
        - Optional[str]: Error message if invalid, None otherwise
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[getattr(settings, 'JWT_ALGORITHM', 'HS256')]
        )
        
        # Get user from token
        user_id = payload.get('user_id')
        if not user_id:
            return False, None, "Invalid token: missing user_id"
        
        # Check if user exists
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                return False, None, "User account is disabled"
        except User.DoesNotExist:
            return False, None, "User not found"
        
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, "Token has expired"
    except jwt.InvalidTokenError:
        return False, None, "Invalid token"
    except Exception as e:
        return False, None, f"Error validating token: {str(e)}"


def get_user_from_token(token: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Extract and return the user from a JWT token.
    
    Args:
        token: The JWT token
        
    Returns:
        Tuple containing:
        - Optional[User]: The user if token is valid, None otherwise
        - Optional[str]: Error message if invalid, None otherwise
    """
    is_valid, payload, error = validate_token(token)
    
    if not is_valid:
        return None, error
    
    try:
        user_id = payload.get('user_id')
        user = User.objects.get(id=user_id)
        return user, None
    except User.DoesNotExist:
        return None, "User not found"
    except Exception as e:
        return None, f"Error retrieving user: {str(e)}"
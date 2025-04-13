"""
Middleware for the Core application.

This module defines middleware components for handling cross-cutting concerns
such as maintaining context about the current user throughout the request lifecycle.
"""
from threading import local
from typing import Optional, Callable, Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse


# Thread-local storage for user data
_user = local()

# Get the User model
User = get_user_model()


class CurrentUserMiddleware:
    """
    Middleware to store the current user in a thread-local context variable.
    
    This middleware makes the current user available to any code that needs it
    without having to pass the request object through all layers of the application.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """
        Initialize the middleware with the get_response callable.
        
        Args:
            get_response: Callable that takes a request and returns a response
        """
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request through the middleware.
        
        This method is called for each request and:
        1. Stores the authenticated user (if any) in thread-local storage
        2. Calls the next middleware/view
        3. Returns the response
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The HTTP response
        """
        # Store authenticated user in thread-local storage
        _user.value = request.user if request.user.is_authenticated else None
        
        # Call the next middleware/view
        response = self.get_response(request)
        
        # Return the response
        return response
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """
        Get the current user from thread-local storage.
        
        This method can be called from anywhere in the application to get the
        user associated with the current thread (request).
        
        Returns:
            Optional[User]: The current user or None if no user is authenticated
        """
        return getattr(_user, 'value', None)


def get_current_user() -> Optional[User]:
    """
    Convenience function to get the current user from anywhere in the application.
    
    This is a shortcut to CurrentUserMiddleware.get_current_user() to make it
    easier to access the current user.
    
    Returns:
        Optional[User]: The current user or None if no user is authenticated
    """
    return CurrentUserMiddleware.get_current_user()
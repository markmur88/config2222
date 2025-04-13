"""
Custom middleware for the API application.

This module defines middleware classes that handle cross-cutting concerns
such as logging, authentication, and request/response processing.
"""
import logging
import time
import json
from typing import Any, Callable, Optional, Dict, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin


# Configure logger
logger = logging.getLogger("django")


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all unhandled exceptions.
    
    This middleware captures any unhandled exceptions that occur during request
    processing and logs them with detailed information to help with debugging.
    """
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """
        Process and log exceptions that occur during request handling.
        
        Args:
            request: The HTTP request being processed
            exception: The exception that was raised
            
        Returns:
            Optional[HttpResponse]: None to allow other middleware to handle the exception,
                                   or a response to short-circuit the middleware chain
        """
        # Log the exception with path and basic information
        logger.error(
            f"Error processing request to {request.path}: {str(exception)}",
            exc_info=True
        )
        
        # Allow the default exception handlers to process the exception
        return None


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log requests and responses.
    
    This middleware logs information about requests and responses,
    which is useful for debugging and auditing purposes.
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """
        Initialize the middleware with the get_response callable.
        
        Args:
            get_response: Callable that takes a request and returns a response
        """
        super().__init__(get_response)
        self.get_response = get_response
        
        # Set up logging based on settings
        self.log_requests = getattr(settings, 'LOG_REQUESTS', False)
        self.log_responses = getattr(settings, 'LOG_RESPONSES', False)
        self.max_body_length = getattr(settings, 'MAX_LOGGED_BODY_LENGTH', 1000)
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Process the request before it reaches the view.
        
        Args:
            request: The HTTP request
            
        Returns:
            Optional[HttpResponse]: None to continue processing,
                                   or a response to short-circuit
        """
        # Add request timestamp for performance monitoring
        request.start_time = time.time()
        
        # Log request if enabled
        if self.log_requests:
            self._log_request(request)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Process the response before it's returned to the client.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            HttpResponse: The processed response
        """
        # Log response if enabled
        if self.log_responses and hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            self._log_response(request, response, duration)
        
        return response
    
    def _log_request(self, request: HttpRequest) -> None:
        """
        Log request details.
        
        Args:
            request: The HTTP request to log
        """
        # Prepare headers
        headers = {k: v for k, v in request.headers.items()}
        
        # Prepare request body if available
        body = None
        if request.body:
            try:
                body = json.loads(request.body)
                # Truncate if too long
                if isinstance(body, dict) and len(str(body)) > self.max_body_length:
                    body = {"truncated": "Request body too large to log"}
            except json.JSONDecodeError:
                body = "<non-JSON body>"
        
        # Log the request
        logger.info(
            f"Request: {request.method} {request.path} - "
            f"User: {request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'} - "
            f"IP: {request.META.get('REMOTE_ADDR')} - "
            f"Headers: {headers} - "
            f"Body: {body or 'No body'}"
        )
    
    def _log_response(self, request: HttpRequest, response: HttpResponse, duration: float) -> None:
        """
        Log response details.
        
        Args:
            request: The HTTP request
            response: The HTTP response to log
            duration: Request processing duration in seconds
        """
        # Prepare response content if available
        content = None
        if hasattr(response, 'content'):
            try:
                if response.get('Content-Type', '').startswith('application/json'):
                    content = json.loads(response.content.decode('utf-8'))
                    # Truncate if too long
                    if isinstance(content, dict) and len(str(content)) > self.max_body_length:
                        content = {"truncated": "Response content too large to log"}
            except (json.JSONDecodeError, UnicodeDecodeError):
                content = "<non-JSON content>"
        
        # Log the response
        logger.info(
            f"Response: {request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s - "
            f"Content: {content or 'No content'}"
        )


class APIErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to standardize API error responses.
    
    This middleware catches exceptions and returns standardized JSON responses
    for API endpoints.
    """
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """
        Process exceptions and return standardized API error responses.
        
        Args:
            request: The HTTP request
            exception: The exception that was raised
            
        Returns:
            Optional[HttpResponse]: JSON response for API errors,
                                   or None for non-API requests
        """
        # Only handle exceptions for API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Log the exception
        logger.error(f"API error in {request.path}: {str(exception)}", exc_info=True)
        
        # Prepare error response
        error_data = {
            "error": {
                "message": str(exception),
                "type": exception.__class__.__name__
            }
        }
        
        # Determine HTTP status code
        status_code = 500
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
        
        # Return JSON response
        return JsonResponse(error_data, status=status_code)
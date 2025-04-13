"""
App configuration for the Authentication application.

This module contains the Django app configuration for the Authentication app,
which manages user authentication, registration, and related functionality.
"""
from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Configuration class for the Authentication app.
    
    Defines app settings and initialization behavior for the app that handles
    user authentication and identity management.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.authentication'
    verbose_name = 'User Authentication'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals to ensure they're registered
        try:
            import api.authentication.signals  # noqa
        except ImportError:
            pass
"""
App configuration for the Sandbox application.

This module contains the Django app configuration for the Sandbox app,
which provides a testing environment for API integrations and bank simulations.
"""
from django.apps import AppConfig


class SandboxConfig(AppConfig):
    """
    Configuration class for the Sandbox app.
    
    Defines app settings and initialization behavior for the app that provides
    a controlled environment for testing banking operations without affecting
    actual banking systems.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.sandbox'
    verbose_name = 'API Sandbox'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals to ensure they're registered
        try:
            import api.sandbox.signals  # noqa
        except ImportError:
            pass
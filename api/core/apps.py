"""
App configuration for the Core application.

This module contains the Django app configuration for the Core app,
which serves as a foundation for shared functionality across the project.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration class for the Core app.
    
    Defines app settings and initialization behavior for the app that provides
    core functionality, shared models, and base classes for the project.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.core'
    verbose_name = 'Core Framework'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals to ensure they're registered
        try:
            import api.core.signals  # noqa
        except ImportError:
            pass
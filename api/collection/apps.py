"""
App configuration for the Collection application.

This module contains the Django app configuration for the Collection app,
which manages bank collections, collection requests, and related functionality.
"""
from django.apps import AppConfig


class CollectionConfig(AppConfig):
    """
    Configuration class for the Collection app.
    
    Defines app settings and initialization behavior for the app that handles
    collections management, tracking and processing.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.collection'
    verbose_name = 'Collection Management'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals to ensure they're registered
        try:
            import api.collection.signals  # noqa
        except ImportError:
            pass
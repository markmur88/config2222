"""
App configuration for the Accounts application.

This module contains the Django app configuration for the Accounts app,
which handles user authentication and account management.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration class for the Accounts app.
    
    Defines app settings such as the default auto field type and app name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.accounts'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals or run other initialization code here if needed
        pass
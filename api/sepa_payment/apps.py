"""
App configuration for the SEPA Payment application.

This module contains the Django app configuration for the SEPA Payment app,
which handles SEPA (Single Euro Payments Area) payment operations.
"""
from django.apps import AppConfig


class SepaPaymentConfig(AppConfig):
    """
    Configuration class for the SEPA Payment app.
    
    Defines app settings and initialization behavior for the app that provides
    functionality for processing SEPA credit transfers and direct debits.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.sepa_payment'
    verbose_name = 'SEPA Payment Processing'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method is called when Django starts and can be used to 
        register signals or perform other initialization tasks.
        """
        # Import signals to ensure they're registered
        try:
            import api.sepa_payment.signals  # noqa
        except ImportError:
            pass
"""
App configuration for the SEPA Credit Transfer (SCT) application.
"""
from django.apps import AppConfig


class SctConfig(AppConfig):
    """
    Configuration class for the SEPA Credit Transfer app.
    Defines the default auto field type and app name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.sct'
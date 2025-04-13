"""
Admin configuration for SEPA Credit Transfer (SCT) models.
This module registers all SCT-related models to the Django admin interface.
"""
from django.contrib import admin
from api.sct.models import (
    CategoryPurpose, ServiceLevel, LocalInstrument,
    SepaCreditTransferRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest,
    ErrorResponse,
)

# Register the models with the admin site
admin.site.register(CategoryPurpose)
admin.site.register(ServiceLevel)
admin.site.register(LocalInstrument)
admin.site.register(SepaCreditTransferRequest)
admin.site.register(SepaCreditTransferResponse)
admin.site.register(SepaCreditTransferDetailsResponse)
admin.site.register(SepaCreditTransferUpdateScaRequest)
admin.site.register(ErrorResponse)
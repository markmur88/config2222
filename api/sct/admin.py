from django.contrib import admin
from api.sct.models import (
    CategoryPurpose, ServiceLevel, LocalInstrument,
    SepaCreditTransferRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest,
    ErrorResponse,
)

# Registrar los modelos
admin.site.register(CategoryPurpose)
admin.site.register(ServiceLevel)
admin.site.register(LocalInstrument)
admin.site.register(SepaCreditTransferRequest)
admin.site.register(SepaCreditTransferResponse)
admin.site.register(SepaCreditTransferDetailsResponse)
admin.site.register(SepaCreditTransferUpdateScaRequest)
admin.site.register(ErrorResponse)
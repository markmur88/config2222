from django.db import models
from api.core.choices import SANDBOX_STATUS_CHOICES
from api.core.models import CoreModel

class IncomingCollection(CoreModel, models.Model):
    reference_id = models.CharField(max_length=100, unique=True)  # ID de referencia del banco
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")  # ISO 4217
    sender_name = models.CharField(max_length=255)
    sender_iban = models.CharField(max_length=34)
    recipient_iban = models.CharField(max_length=34)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=SANDBOX_STATUS_CHOICES, default="PENDING")

    def __str__(self):
        return f"{self.reference_id} - {self.amount} {self.currency}"

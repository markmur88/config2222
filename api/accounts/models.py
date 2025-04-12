import uuid
from django.db import models
from django.contrib.auth.models import User
from api.core.choices import ACCOUNT_TYPES, ACCOUNT_STATUS, TYPE
from api.core.models import CoreModel, IBAN

class Account(CoreModel, models.Model):
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, choices=ACCOUNT_STATUS, default='active')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="EUR")
    iban = models.ForeignKey(IBAN, on_delete=models.CASCADE, null=False, blank=False)  # IBAN principal
    type = models.CharField(max_length=30, choices=ACCOUNT_TYPES, default='current_account')
    is_main = models.CharField(max_length=8, choices=TYPE, default='main')
    
    def __str__(self):
        return f"{self.name}"
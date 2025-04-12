import uuid
from django.db import models

from api.accounts.models import Account
from api.core.choices import DIRECTION_CHOICES, STATUS_CHOICES, TRANSFER_TYPES, TYPE_STRATEGIES
from api.core.models import CoreModel, Debtor
from api.collection.models import Collection

class Transaction(CoreModel, models.Model):
    reference = models.UUIDField(default=uuid.uuid4, editable=False)  # Referencia única
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transaction_set')
    source_account = models.CharField(max_length=50)
    destination_account = models.CharField(max_length=50)    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    local_iban = models.CharField(max_length=34)  # IBAN local
    currency = models.CharField(max_length=3, default="EUR")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    request_date = models.DateTimeField()  # Fecha de solicitud
    execution_date = models.DateTimeField()  # Fecha de ejecución
    accounting_date = models.DateTimeField(null=True, blank=True)  # Fecha de contabilidad
    counterparty_name = models.CharField(max_length=255)  # Nombre del beneficiario
    internal_note = models.TextField(blank=True, null=True)  # Nota interna
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')  # Estado
    custom_id = models.CharField(max_length=256, blank=True, null=True)  # ID personalizado
    custom_metadata = models.TextField(blank=True, null=True)  # Metadatos personalizados
    attachment_count = models.IntegerField(default=0)  # Número de archivos adjuntos
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # Garantizar unicidad
    
    def __str__(self):
        return f"{self.source_account} -> {self.destination_account} | {self.amount} {self.currency}"

# SEPA
class SEPA(CoreModel, models.Model):
    # Identificadores únicos
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, editable=False)  # Referencia única
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    custom_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    end_to_end_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Relación con la cuenta
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions_sepa_set')
    
    # Información de la transacción
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")

    # Información del beneficiario
    beneficiary_name = models.ForeignKey(Debtor, on_delete=models.CASCADE)  # Nombre del beneficiario

    # Detalles adicionales
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, null=True, blank=True)
    type_strategy = models.CharField(max_length=20, choices=TYPE_STRATEGIES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')  # Estado
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    failure_code = models.CharField(max_length=50, blank=True, null=True)  # Código de fallo
    message = models.CharField(max_length=20, blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)  # Nota interna
    custom_metadata = models.TextField(blank=True, null=True)  # Metadatos personalizados

    # Fechas
    scheduled_date = models.DateField(null=True, blank=True)  # Fecha programada
    #custom_created_at = models.DateTimeField(auto_now_add=True)  # Campo renombrado
    request_date = models.DateTimeField(auto_now_add=True)  # Fecha de solicitud
    execution_date = models.DateTimeField(null=True, blank=True)  # Fecha de ejecución
    accounting_date = models.DateTimeField(null=True, blank=True)  # Fecha de contabilidad

    # Archivos adjuntos y usuario
    #attachment_count = models.IntegerField(default=0)  # Número de archivos adjuntos

    def __str__(self):
        return f"{self.transaction_id} | {self.idempotency_key}"

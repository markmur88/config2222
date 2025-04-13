import uuid
from django.db import models
from api.core.choices import DIRECTION_CHOICES, TRANSFER_TYPES, TYPE_STRATEGIES, STATUS_CHOICES, NAME, IBAN, BIC, BANK
from api.core.middleware import CurrentUserMiddleware
from api.authentication.models import CustomUser

class Transfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, editable=False)  # Referencia única
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    source_account = models.CharField(max_length=50)
    destination_account = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')  # ISO 4217 (ej: EUR)
    local_iban = models.CharField(max_length=34)  # IBAN local
    account = models.CharField(max_length=255)
    beneficiary_iban = models.CharField(max_length=34)  # IBAN del beneficiario
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, null=True, blank=True)
    type_strategy = models.CharField(max_length=20, choices=TYPE_STRATEGIES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')  # Estado
    failure_code = models.CharField(max_length=50, blank=True, null=True)  # Código de fallo
    scheduled_date = models.DateField(null=True, blank=True)  # Fecha programada
    message = models.TextField(blank=True, null=True)  # Mensaje adjunto
    end_to_end_id = models.CharField(max_length=35, blank=True, null=True)  # ID único
    internal_note = models.TextField(blank=True, null=True)  # Nota interna
    custom_id = models.CharField(max_length=256, blank=True, null=True)  # ID personalizado
    custom_metadata = models.TextField(blank=True, null=True)  # Metadatos personalizados
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.source_account} -> {self.destination_account} | {self.amount} {self.currency}"

class SepaTransaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    sender_iban = models.CharField(max_length=34)
    recipient_iban = models.CharField(max_length=34)
    recipient_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SEPA2(models.Model):
    # Detalles adicionales Choices
    # transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, null=True, blank=True)
    # type_strategy = models.CharField(max_length=20, choices=TYPE_STRATEGIES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')  # Estado
    # direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
        
    # Identificadores únicos
    reference = models.UUIDField(default=uuid.uuid4, editable=False)  # Referencia única
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    custom_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    end_to_end_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Relación con la cuenta
    account_name = models.CharField(max_length=50, blank=False, null=False, choices=NAME)
    account_iban = models.CharField(max_length=24, blank=False, null=False, choices=IBAN)
    account_bic = models.CharField(max_length=11, blank=False, null=False, choices=BIC)
    account_bank = models.CharField(max_length=50, blank=False, null=False, choices=BANK)
    
    # Información de la transacción
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    
    # Información del beneficiario
    beneficiary_name = models.CharField(max_length=50, blank=False, null=False, choices=NAME)
    beneficiary_iban = models.CharField(max_length=24, blank=False, null=False, choices=IBAN)
    beneficiary_bic = models.CharField(max_length=11, blank=False, null=False, choices=BIC)
    beneficiary_bank = models.CharField(max_length=50, blank=False, null=False, choices=BANK)
    
    # Códigos de error y mensajes
    failure_code = models.CharField(max_length=50, blank=True, null=True)  # Código de fallo
    message = models.CharField(max_length=20, blank=True, null=True)
    internal_note = models.CharField(max_length=10, blank=True, null=True)  # Nota interna
    custom_metadata = models.CharField(max_length=50, blank=True, null=True)  # Metadatos personalizados
    
    # Fechas
    scheduled_date = models.DateField(auto_now_add=True, null=True, blank=True)  # Fecha programada
    request_date = models.DateTimeField(auto_now_add=True)  # Fecha de solicitud
    execution_date = models.DateTimeField(auto_now_add=True)  # Fecha de ejecución
    accounting_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Fecha de contabilidad
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_%(class)s_set")

    def save(self, *args, **kwargs):
        if not self.created_by_id:  # Verifica si el ID de created_by está vacío
            self.created_by = CurrentUserMiddleware.get_current_user()
        if not self.created_by:  # Si no se puede obtener el usuario actual, lanza un error
            raise ValueError("El campo 'created_by' no puede estar vacío.")
        super().save(*args, **kwargs)
    
        



class SEPA3(models.Model):
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    sender_name = models.CharField(max_length=255, choices=NAME)
    sender_iban = models.CharField(max_length=34, choices=IBAN)
    sender_bic = models.CharField(max_length=11, choices=BIC)
    sender_bank = models.CharField(max_length=80, choices=BANK)
    recipient_name = models.CharField(max_length=255, choices=NAME)
    recipient_iban = models.CharField(max_length=34, choices=IBAN)
    recipient_bic = models.CharField(max_length=11, choices=BIC)
    recipient_bank = models.CharField(max_length=80, choices=BANK)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PDNG')  # Estado
    execution_date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=20, blank=True, null=True)
    unstructured_remittance_info = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_%(class)s_set")

    def save(self, *args, **kwargs):
        if not self.created_by_id:  # Verifica si el ID de created_by está vacío
            self.created_by = CurrentUserMiddleware.get_current_user()
        if not self.created_by:  # Si no se puede obtener el usuario actual, lanza un error
            raise ValueError("El campo 'created_by' no puede estar vacío.")
        super().save(*args, **kwargs)
    
        
    def __str__(self):
        return str(self.idempotency_key)

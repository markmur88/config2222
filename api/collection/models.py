from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from api.core.models import Debtor, Core2Model
from api.accounts.models import Account
import uuid
from api.core.choices import SCHEME_CHOICES, COLLECTION_STATUS_CHOICES

# Modelo para la entidad Mandato (mandatos de cobro)
class Mandate(Core2Model, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scheme = models.CharField(max_length=4, choices=SCHEME_CHOICES, null=False, blank=False)
    debtor_name = models.ForeignKey(
        Debtor, on_delete=models.CASCADE, to_field='name', related_name='mandates_by_name'
    )
    debtor_iban = models.ForeignKey(
        Debtor, on_delete=models.CASCADE, to_field='iban', related_name='mandates_by_iban'
    )
    signature_date = models.DateField()
    contract_reference = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.debtor_name} - {self.reference} - {self.scheme}"
 
class Collection(Core2Model, models.Model):  # Eliminamos la herencia de Mandate
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Asegúrate de que sea UUIDField
    mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE, related_name='collections')
    scheduled_date = models.DateField()
    local_iban = models.OneToOneField(  # Cambiamos ForeignKey a OneToOneField
        Account, on_delete=models.CASCADE, to_field='name'
    )  # IBAN de la cuenta local
    #status = models.CharField(max_length=10, choices=COLLECTION_STATUS_CHOICES, default='pending')  # Descomentamos este campo
    message = models.CharField(max_length=20, blank=True, null=True)
    end_to_end_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    internal_note = models.CharField(max_length=256, blank=True, null=True)
    custom_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    custom_metadata = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Collection {self.id} - {self.mandate} - {self.scheduled_date}"
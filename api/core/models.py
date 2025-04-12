from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from api.core.choices import TYPE, ACCOUNT_STATUS
from api.core.middleware import CurrentUserMiddleware
from api.core.mixin import UppercaseCharFieldMixin
from api.authentication.models import CustomUser
from api.transfers.models import SEPA3

class CoreModel(UppercaseCharFieldMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Cambiado a DateTimeField
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_%(class)s_set")

    def save(self, *args, **kwargs):
        # Registra el usuario actual si está disponible en el middleware
        if not self.created_by_id:  # Cambiado a created_by_id
            self.created_by = CurrentUserMiddleware.get_current_user()
        if not self.created_by:  # Cambiado a created_by
            raise ValueError("El campo 'created_by' no puede estar vacío.")
        super().save(*args, **kwargs)
    
    class Meta:
        abstract = True

class Core2Model(UppercaseCharFieldMixin, models.Model):
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="created_%(class)s_set")

    def save(self, *args, **kwargs):
        if not self.created_by_id:  # Verifica si el ID de created_by está vacío
            self.created_by = CurrentUserMiddleware.get_current_user()
        if not self.created_by:  # Si no se puede obtener el usuario actual, lanza un error
            raise ValueError("El campo 'created_by' no puede estar vacío.")
        super().save(*args, **kwargs)
    
    class Meta:
        abstract = True

# Modelo para la entidad IBAN (IBANs asociados a una cuenta)
class IBAN(CoreModel, models.Model):
    iban = models.CharField(max_length=34, unique=True)  # Índice único agregado
    bic = models.CharField(max_length=11, blank=False, null=False)  # Código BIC
    bank_name = models.CharField(max_length=40, blank=False, null=False)  # Nombre del banco
    status = models.CharField(max_length=8, choices=ACCOUNT_STATUS, default='active')  # Estado (active, inactive)
    type = models.CharField(max_length=7, choices=TYPE, default='main')  # Tipo (main, virtual)
    allow_collections = models.BooleanField(default=True)  # Permite cobros
    is_deleted = models.BooleanField(default=False)  # Indica si está eliminado

    def __str__(self):
        return f"{self.iban} ({self.bank_name})"


# Modelo para la entidad Debtor (Deudor)
class Debtor(CoreModel, models.Model):
    name = models.CharField(max_length=255, unique=True)  # Nombre del deudor
    iban = models.OneToOneField(IBAN, on_delete=models.CASCADE, null=False, blank=False)  # IBAN principal   
    street = models.CharField(max_length=30, blank=False, null=False)  # Calle
    building_number = models.CharField(max_length=10, null=True, blank=True)  # Número del edificio
    postal_code = models.CharField(max_length=8, blank=False, null=False)  # Código postal
    city = models.CharField(max_length=80)  # Ciudad
    country = models.CharField(max_length=2)  # Código ISO 3166-1 alpha-2 (FR, DE, etc.)

    def __str__(self):
        return f"Debtor {self.name} ({self.iban})"
    

class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.TextField()
    messageId = models.AutoField(primary_key=True)
    
    def __str__(self):
        return str(self.messageId)

class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    code = models.IntegerField()
    message = models.TextField()
    def __str__(self):
        return str(self.message_id)

class TransactionStatus(models.Model):
    transaction_status = models.CharField(max_length=4, default='PDNG')
    description = models.CharField(max_length=250, blank=True)
    
    def __str__(self):
        return f'{self.transaction_status} - {self.description}'

class StatusResponse(models.Model):
    category = models.CharField(max_length=20, blank=False)
    code = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)
    text = models.CharField(max_length=50)

class PaymentResponse(models.Model):
    payment_id = models.ForeignKey(SEPA3, on_delete=models.CASCADE)
    transaction_status = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)















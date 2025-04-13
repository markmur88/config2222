"""
Database models for the Collection application.

This module defines models for managing collections and mandates,
including the relationships between debtors, accounts, and collection requests.
"""
import uuid
from decimal import Decimal
from typing import Any

from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from api.accounts.models import Account
from api.core.choices import SCHEME_CHOICES, COLLECTION_STATUS_CHOICES
from api.core.models import Debtor, Core2Model


class Mandate(Core2Model, models.Model):
    """
    Model representing a direct debit mandate.
    
    A mandate is an authorization from a debtor allowing a creditor
    to collect money from their account.
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique identifier for the mandate")
    )
    reference = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Unique reference number for the mandate")
    )
    scheme = models.CharField(
        max_length=4, 
        choices=SCHEME_CHOICES, 
        null=False, 
        blank=False,
        help_text=_("The direct debit scheme (e.g., CORE, B2B)")
    )
    debtor_name = models.ForeignKey(
        Debtor, 
        on_delete=models.CASCADE, 
        to_field='name', 
        related_name='mandates_by_name',
        help_text=_("The name of the debtor who signed the mandate")
    )
    debtor_iban = models.ForeignKey(
        Debtor, 
        on_delete=models.CASCADE, 
        to_field='iban', 
        related_name='mandates_by_iban',
        help_text=_("The IBAN of the debtor's account")
    )
    signature_date = models.DateField(
        help_text=_("Date when the mandate was signed by the debtor")
    )
    contract_reference = models.CharField(
        max_length=30, 
        blank=True, 
        null=True,
        help_text=_("Reference to the underlying contract")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this mandate is currently active")
    )
    
    class Meta:
        """
        Metadata for the Mandate model.
        """
        verbose_name = _("mandate")
        verbose_name_plural = _("mandates")
        ordering = ['-signature_date']
        indexes = [
            models.Index(fields=['scheme']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the mandate.
        
        Returns:
            str: A human-readable string representing the mandate
        """
        return f"{self.debtor_name} - {self.reference} - {self.scheme}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save method to perform additional operations.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        # Perform any custom operations before saving
        super().save(*args, **kwargs)


class Collection(Core2Model, models.Model):
    """
    Model representing a collection request.
    
    A collection is a request to collect money from a debtor's account
    based on an existing mandate.
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique identifier for the collection")
    )
    mandate = models.ForeignKey(
        Mandate, 
        on_delete=models.CASCADE, 
        related_name='collections',
        help_text=_("The mandate authorizing this collection")
    )
    scheduled_date = models.DateField(
        help_text=_("Date when the collection should be executed")
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Amount to be collected")
    )
    local_iban = models.ForeignKey(  # Changed from OneToOneField to ForeignKey
        Account, 
        on_delete=models.CASCADE, 
        to_field='name',
        help_text=_("The account where funds will be credited")
    )
    status = models.CharField(
        max_length=10, 
        choices=COLLECTION_STATUS_CHOICES, 
        default='pending',
        help_text=_("Current status of the collection")
    )
    message = models.CharField(
        max_length=140,  # Increased from 20 to allow more meaningful messages
        blank=True, 
        null=True,
        help_text=_("Message to be shown to the debtor")
    )
    end_to_end_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Unique end-to-end identifier for the transaction")
    )
    internal_note = models.TextField(  # Changed from CharField to TextField
        blank=True, 
        null=True,
        help_text=_("Notes for internal use only")
    )
    custom_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Custom identifier for external systems")
    )
    custom_metadata = models.JSONField(  # Changed from TextField to JSONField
        blank=True, 
        null=True,
        help_text=_("Additional metadata in JSON format")
    )
    
    class Meta:
        """
        Metadata for the Collection model.
        """
        verbose_name = _("collection")
        verbose_name_plural = _("collections")
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the collection.
        
        Returns:
            str: A human-readable string representing the collection
        """
        return f"Collection {self.id} - {self.mandate} - {self.scheduled_date}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save method to perform additional operations.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Raises:
            ValidationError: If the mandate is not active
        """
        from django.core.exceptions import ValidationError
        
        # Check if the mandate is active
        if not self.mandate.is_active:
            raise ValidationError(_("Cannot create a collection with an inactive mandate"))
        
        # Perform any custom operations before saving
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self) -> bool:
        """
        Check if the collection is pending.
        
        Returns:
            bool: True if collection status is 'pending', False otherwise
        """
        return self.status == 'pending'
    
    @property
    def debtor_name(self) -> str:
        """
        Get the debtor name from the associated mandate.
        
        Returns:
            str: The name of the debtor
        """
        return str(self.mandate.debtor_name)
    
    @property
    def debtor_iban(self) -> str:
        """
        Get the debtor IBAN from the associated mandate.
        
        Returns:
            str: The IBAN of the debtor's account
        """
        return str(self.mandate.debtor_iban)
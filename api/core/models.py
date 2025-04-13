"""
Core models for the application.

This module defines foundational models that are used throughout
the application, including base models, common data structures, and 
shared entities.
"""
import uuid
from typing import Any, Optional, Dict, Union

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from api.core.choices import TYPE, ACCOUNT_STATUS
from api.core.middleware import CurrentUserMiddleware, get_current_user
from api.core.mixin import UppercaseCharFieldMixin


class CoreModel(UppercaseCharFieldMixin, models.Model):
    """
    Base model providing common fields and functionality for all models.
    
    This abstract model provides:
    - UUID primary key
    - Created/updated timestamps
    - User tracking
    - Uppercase character field conversion
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique identifier for this record")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this record was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When this record was last updated")
    )
    created_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_%(class)s_set",
        help_text=_("User who created this record")
    )
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save method to automatically set created_by.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        
        Raises:
            ValueError: If created_by cannot be determined
        """
        # Set the current user as created_by if not already set
        if not self.created_by_id:
            self.created_by = get_current_user()
            
            # If still no user is available, raise an error
            if not self.created_by and not kwargs.get('skip_user_validation', False):
                raise ValueError(_("The 'created_by' field cannot be empty."))
                
        # Remove our custom kwarg if it exists
        if 'skip_user_validation' in kwargs:
            del kwargs['skip_user_validation']
            
        # Call parent save method
        super().save(*args, **kwargs)
    
    class Meta:
        """
        Metadata for the CoreModel.
        """
        abstract = True


class Core2Model(UppercaseCharFieldMixin, models.Model):
    """
    Lightweight base model with user tracking but no timestamps.
    
    This abstract model provides:
    - User tracking
    - Uppercase character field conversion
    But does not include:
    - UUID primary key
    - Created/updated timestamps
    """
    created_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_%(class)s_set",
        help_text=_("User who created this record")
    )
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save method to automatically set created_by.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        
        Raises:
            ValueError: If created_by cannot be determined
        """
        # Set the current user as created_by if not already set
        if not self.created_by_id:
            self.created_by = get_current_user()
            
            # If still no user is available, raise an error
            if not self.created_by and not kwargs.get('skip_user_validation', False):
                raise ValueError(_("The 'created_by' field cannot be empty."))
                
        # Remove our custom kwarg if it exists
        if 'skip_user_validation' in kwargs:
            del kwargs['skip_user_validation']
            
        # Call parent save method
        super().save(*args, **kwargs)
    
    class Meta:
        """
        Metadata for the Core2Model.
        """
        abstract = True


class IBAN(CoreModel):
    """
    Model for International Bank Account Numbers (IBANs).
    
    Stores IBAN data along with related bank information and
    configuration settings.
    """
    iban = models.CharField(
        max_length=34, 
        unique=True,
        help_text=_("International Bank Account Number")
    )
    bic = models.CharField(
        max_length=11, 
        blank=False, 
        null=False,
        help_text=_("Bank Identifier Code (SWIFT)")
    )
    bank_name = models.CharField(
        max_length=40, 
        blank=False, 
        null=False,
        help_text=_("Name of the financial institution")
    )
    status = models.CharField(
        max_length=8, 
        choices=ACCOUNT_STATUS, 
        default='active',
        help_text=_("Current status of this IBAN")
    )
    type = models.CharField(
        max_length=7, 
        choices=TYPE, 
        default='main',
        help_text=_("Type of IBAN (main or virtual)")
    )
    allow_collections = models.BooleanField(
        default=True,
        help_text=_("Whether this IBAN can be used for collections")
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text=_("Soft delete flag")
    )
    
    class Meta:
        """
        Metadata for the IBAN model.
        """
        verbose_name = _("IBAN")
        verbose_name_plural = _("IBANs")
        ordering = ['iban']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the IBAN.
        
        Returns:
            str: A formatted string with IBAN and bank name
        """
        return f"{self.iban} ({self.bank_name})"
    
    def is_active(self) -> bool:
        """
        Check if the IBAN is active.
        
        Returns:
            bool: True if the IBAN is active, False otherwise
        """
        return self.status == 'active' and not self.is_deleted


class Debtor(CoreModel):
    """
    Model for debtor information.
    
    Stores details about entities that can be debited,
    including their contact information and associated IBAN.
    """
    name = models.CharField(
        max_length=255, 
        unique=True,
        help_text=_("Name of the debtor (individual or organization)")
    )
    iban = models.OneToOneField(
        IBAN, 
        on_delete=models.CASCADE, 
        null=False, 
        blank=False,
        help_text=_("Primary IBAN for this debtor")
    )
    street = models.CharField(
        max_length=30, 
        blank=False, 
        null=False,
        help_text=_("Street name")
    )
    building_number = models.CharField(
        max_length=10, 
        null=True, 
        blank=True,
        help_text=_("Building or house number")
    )
    postal_code = models.CharField(
        max_length=8, 
        blank=False, 
        null=False,
        help_text=_("Postal or ZIP code")
    )
    city = models.CharField(
        max_length=80,
        help_text=_("City or town")
    )
    country = models.CharField(
        max_length=2,
        help_text=_("ISO 3166-1 alpha-2 country code (e.g., FR, DE)")
    )
    
    class Meta:
        """
        Metadata for the Debtor model.
        """
        verbose_name = _("Debtor")
        verbose_name_plural = _("Debtors")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['country', 'city']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the Debtor.
        
        Returns:
            str: A formatted string with name and IBAN
        """
        return f"{self.name} ({self.iban.iban})"
    
    @property
    def full_address(self) -> str:
        """
        Get the full address as a formatted string.
        
        Returns:
            str: Complete address with all components
        """
        building = f" {self.building_number}" if self.building_number else ""
        return f"{self.street}{building}, {self.postal_code} {self.city}, {self.country}"


class ErrorResponse(models.Model):
    """
    Model for storing API error responses.
    
    Used to track and standardize error messages across the application.
    """
    code = models.IntegerField(
        help_text=_("Error code")
    )
    message = models.TextField(
        help_text=_("Detailed error message")
    )
    messageId = models.AutoField(
        primary_key=True,
        help_text=_("Unique identifier for this error message")
    )
    
    class Meta:
        """
        Metadata for the ErrorResponse model.
        """
        verbose_name = _("Error Response")
        verbose_name_plural = _("Error Responses")
    
    def __str__(self) -> str:
        """
        String representation of the ErrorResponse.
        
        Returns:
            str: The message ID
        """
        return f"Error {self.code}: {self.message}"


class Message(models.Model):
    """
    Model for storing application messages.
    
    Used for system notifications, alerts, and other messages.
    """
    message_id = models.AutoField(
        primary_key=True,
        help_text=_("Unique identifier for this message")
    )
    code = models.IntegerField(
        help_text=_("Message code for categorization")
    )
    message = models.TextField(
        help_text=_("Message content")
    )
    
    class Meta:
        """
        Metadata for the Message model.
        """
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
    
    def __str__(self) -> str:
        """
        String representation of the Message.
        
        Returns:
            str: The message ID
        """
        return f"Message {self.message_id}: {self.code}"


class TransactionStatus(models.Model):
    """
    Model for transaction status codes and descriptions.
    
    Provides a centralized way to manage transaction statuses.
    """
    transaction_status = models.CharField(
        max_length=4, 
        default='PDNG',
        help_text=_("Status code (e.g., PDNG, ACCP)")
    )
    description = models.CharField(
        max_length=250, 
        blank=True,
        help_text=_("Description of what this status means")
    )
    
    class Meta:
        """
        Metadata for the TransactionStatus model.
        """
        verbose_name = _("Transaction Status")
        verbose_name_plural = _("Transaction Statuses")
        ordering = ['transaction_status']
    
    def __str__(self) -> str:
        """
        String representation of the TransactionStatus.
        
        Returns:
            str: Status code and description
        """
        return f'{self.transaction_status} - {self.description}'


class StatusResponse(models.Model):
    """
    Model for detailed status responses.
    
    Links transaction statuses with categories and explanatory text.
    """
    category = models.CharField(
        max_length=20, 
        blank=False,
        help_text=_("Category of the status (e.g., 'payment', 'transfer')")
    )
    code = models.ForeignKey(
        TransactionStatus, 
        on_delete=models.CASCADE,
        help_text=_("Reference to the transaction status code")
    )
    text = models.CharField(
        max_length=50,
        help_text=_("User-friendly status message")
    )
    
    class Meta:
        """
        Metadata for the StatusResponse model.
        """
        verbose_name = _("Status Response")
        verbose_name_plural = _("Status Responses")
    
    def __str__(self) -> str:
        """
        String representation of the StatusResponse.
        
        Returns:
            str: Category and status information
        """
        return f"{self.category}: {self.code.transaction_status} - {self.text}"


class PaymentResponse(models.Model):
    """
    Model for tracking payment responses.
    
    Records the status of payments processed by the system.
    """
    payment_id = models.ForeignKey(
        'transfers.SEPA3', 
        on_delete=models.CASCADE,
        help_text=_("Reference to the payment")
    )
    transaction_status = models.ForeignKey(
        TransactionStatus, 
        on_delete=models.CASCADE,
        help_text=_("Current status of the payment")
    )
    
    class Meta:
        """
        Metadata for the PaymentResponse model.
        """
        verbose_name = _("Payment Response")
        verbose_name_plural = _("Payment Responses")
    
    def __str__(self) -> str:
        """
        String representation of the PaymentResponse.
        
        Returns:
            str: Payment ID and status
        """
        return f"Payment {self.payment_id} - Status: {self.transaction_status.transaction_status}"
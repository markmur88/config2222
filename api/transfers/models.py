"""
Models for the Transfers application.

This module defines database models for tracking money transfers,
including SEPA transfers and other transaction types.
"""
import uuid
from typing import Any, Dict, Optional, Union

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from api.core.choices import (
    DIRECTION_CHOICES, TRANSFER_TYPES, TYPE_STRATEGIES, 
    STATUS_CHOICES, NAME, IBAN, BIC, BANK
)
from api.core.middleware import get_current_user
from api.authentication.models import CustomUser


class Transfer(models.Model):
    """
    Model for standard money transfers.
    
    Records details of money transfers between accounts, including
    source and destination information, amount, and status.
    """
    # Unique identifiers
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique identifier for this transfer")
    )
    reference = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique reference for this transfer")
    )
    idempotency_key = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True,
        help_text=_("Key to ensure the transfer is processed exactly once")
    )
    
    # Account information
    source_account = models.CharField(
        max_length=50,
        help_text=_("Source account identifier")
    )
    destination_account = models.CharField(
        max_length=50,
        help_text=_("Destination account identifier")
    )
    local_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the local account")
    )
    account = models.CharField(
        max_length=255,
        help_text=_("Account reference")
    )
    beneficiary_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the beneficiary")
    )
    
    # Transfer details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Transfer amount")
    )
    currency = models.CharField(
        max_length=3, 
        default='EUR',
        help_text=_("ISO 4217 currency code (e.g., EUR)")
    )
    transfer_type = models.CharField(
        max_length=20, 
        choices=TRANSFER_TYPES, 
        null=True, 
        blank=True,
        help_text=_("Type of transfer (standard or instant)")
    )
    type_strategy = models.CharField(
        max_length=20, 
        choices=TYPE_STRATEGIES,
        help_text=_("Strategy for handling the transfer type")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transfer")
    )
    failure_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text=_("Code indicating the reason for failure")
    )
    
    # Dates
    scheduled_date = models.DateField(
        null=True, 
        blank=True,
        help_text=_("Date when the transfer is scheduled")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the transfer was created")
    )
    
    # Additional information
    message = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Message attached to the transfer")
    )
    end_to_end_id = models.CharField(
        max_length=35, 
        blank=True, 
        null=True,
        help_text=_("End-to-end identifier for the transfer")
    )
    internal_note = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Internal notes about this transfer")
    )
    custom_id = models.CharField(
        max_length=256, 
        blank=True, 
        null=True,
        help_text=_("Custom identifier for this transfer")
    )
    custom_metadata = models.JSONField(
        blank=True, 
        null=True,
        help_text=_("Additional metadata in JSON format")
    )
    
    class Meta:
        """
        Metadata for the Transfer model.
        """
        verbose_name = _("Transfer")
        verbose_name_plural = _("Transfers")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the Transfer.
        
        Returns:
            str: A formatted string with source, destination, and amount
        """
        return f"{self.source_account} → {self.destination_account} | {self.amount} {self.currency}"
    
    def is_completed(self) -> bool:
        """
        Check if the transfer is completed.
        
        Returns:
            bool: True if the transfer is completed, False otherwise
        """
        return self.status in ['ACSC', 'ACCC']
    
    def is_pending(self) -> bool:
        """
        Check if the transfer is pending.
        
        Returns:
            bool: True if the transfer is pending, False otherwise
        """
        return self.status in ['PDNG', 'ACSP', 'ACWP']


class SepaTransaction(models.Model):
    """
    Model for SEPA transactions.
    
    Records details of SEPA (Single Euro Payments Area) transactions,
    including sender and recipient information.
    """
    transaction_id = models.CharField(
        max_length=255, 
        unique=True,
        help_text=_("Unique transaction identifier")
    )
    sender_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the sender")
    )
    recipient_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the recipient")
    )
    recipient_name = models.CharField(
        max_length=255,
        help_text=_("Name of the recipient")
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Transaction amount")
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text=_("Currency code (normally EUR for SEPA)")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transaction")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the transaction was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the transaction was last updated")
    )
    
    class Meta:
        """
        Metadata for the SepaTransaction model.
        """
        verbose_name = _("SEPA Transaction")
        verbose_name_plural = _("SEPA Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the SEPA Transaction.
        
        Returns:
            str: A formatted string with transaction ID and amount
        """
        return f"SEPA: {self.transaction_id} | {self.recipient_name} | {self.amount} {self.currency}"


class SEPA2(models.Model):
    """
    Model for SEPA2 transfers.
    
    Records detailed information for SEPA transfers, including
    account and beneficiary details, with user tracking.
    """
    # Unique identifiers
    reference = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique reference for this transfer")
    )
    idempotency_key = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Ensures uniqueness of transaction processing")
    )
    custom_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Custom unique identifier")
    )
    end_to_end_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("End-to-end identifier for SEPA transfers")
    )
    
    # Account information
    account_name = models.CharField(
        max_length=50, 
        blank=False, 
        null=False, 
        choices=NAME,
        help_text=_("Name of the account holder")
    )
    account_iban = models.CharField(
        max_length=24, 
        blank=False, 
        null=False, 
        choices=IBAN,
        help_text=_("IBAN of the account")
    )
    account_bic = models.CharField(
        max_length=11, 
        blank=False, 
        null=False, 
        choices=BIC,
        help_text=_("BIC of the account bank")
    )
    account_bank = models.CharField(
        max_length=50, 
        blank=False, 
        null=False, 
        choices=BANK,
        help_text=_("Name of the account bank")
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text=_("Transfer amount")
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text=_("Currency code (normally EUR for SEPA)")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transfer")
    )
    purpose_code = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        help_text=_("ISO 20022 purpose code")
    )
    
    # Beneficiary information
    beneficiary_name = models.CharField(
        max_length=50, 
        blank=False, 
        null=False, 
        choices=NAME,
        help_text=_("Name of the beneficiary")
    )
    beneficiary_iban = models.CharField(
        max_length=24, 
        blank=False, 
        null=False, 
        choices=IBAN,
        help_text=_("IBAN of the beneficiary")
    )
    beneficiary_bic = models.CharField(
        max_length=11, 
        blank=False, 
        null=False, 
        choices=BIC,
        help_text=_("BIC of the beneficiary bank")
    )
    beneficiary_bank = models.CharField(
        max_length=50, 
        blank=False, 
        null=False, 
        choices=BANK,
        help_text=_("Name of the beneficiary bank")
    )
    
    # Error and additional information
    failure_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text=_("Code indicating the reason for failure")
    )
    message = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text=_("Message related to the transfer")
    )
    internal_note = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Internal notes about this transfer")
    )
    custom_metadata = models.JSONField(
        blank=True, 
        null=True,
        help_text=_("Additional metadata in JSON format")
    )
    
    # Dates
    scheduled_date = models.DateField(
        auto_now_add=False, 
        null=True, 
        blank=True,
        help_text=_("Date when the transfer is scheduled")
    )
    request_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the transfer was requested")
    )
    execution_date = models.DateTimeField(
        default=timezone.now,
        help_text=_("When the transfer was/will be executed")
    )
    accounting_date = models.DateTimeField(
        auto_now_add=False, 
        null=True, 
        blank=True,
        help_text=_("When the transfer was recorded in accounting")
    )
    
    # User tracking
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="created_%(class)s_set",
        help_text=_("User who created this transfer")
    )
    
    class Meta:
        """
        Metadata for the SEPA2 model.
        """
        verbose_name = _("SEPA2 Transfer")
        verbose_name_plural = _("SEPA2 Transfers")
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status']),
            models.Index(fields=['request_date']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the SEPA2 Transfer.
        
        Returns:
            str: A formatted string with accounts and amount
        """
        return f"{self.account_name} → {self.beneficiary_name} | {self.amount} {self.currency}"
    
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


class SEPA3(models.Model):
    """
    Model for SEPA3 transfers.
    
    An enhanced version of SEPA transfers with additional fields
    and improved structure.
    """
    # Unique identifiers
    idempotency_key = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        help_text=_("Ensures uniqueness of transaction processing")
    )
    
    # Sender information
    sender_name = models.CharField(
        max_length=255, 
        choices=NAME,
        help_text=_("Name of the sender")
    )
    sender_iban = models.CharField(
        max_length=34, 
        choices=IBAN,
        help_text=_("IBAN of the sender")
    )
    sender_bic = models.CharField(
        max_length=11, 
        choices=BIC,
        help_text=_("BIC of the sender's bank")
    )
    sender_bank = models.CharField(
        max_length=80, 
        choices=BANK,
        help_text=_("Name of the sender's bank")
    )
    
    # Recipient information
    recipient_name = models.CharField(
        max_length=255, 
        choices=NAME,
        help_text=_("Name of the recipient")
    )
    recipient_iban = models.CharField(
        max_length=34, 
        choices=IBAN,
        help_text=_("IBAN of the recipient")
    )
    recipient_bic = models.CharField(
        max_length=11, 
        choices=BIC,
        help_text=_("BIC of the recipient's bank")
    )
    recipient_bank = models.CharField(
        max_length=80, 
        choices=BANK,
        help_text=_("Name of the recipient's bank")
    )
    
    # Transfer details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Transfer amount")
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text=_("Currency code (normally EUR for SEPA)")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transfer")
    )
    
    # Additional information
    reference = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text=_("Reference for the transfer")
    )
    unstructured_remittance_info = models.CharField(
        max_length=140, 
        blank=True, 
        null=True,
        help_text=_("Unstructured remittance information")
    )
    
    # Dates and tracking
    execution_date = models.DateField(
        default=timezone.now,
        help_text=_("Date when the transfer should be executed")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the transfer was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the transfer was last updated")
    )
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name="created_%(class)s_set",
        help_text=_("User who created this transfer")
    )
    
    class Meta:
        """
        Metadata for the SEPA3 model.
        """
        verbose_name = _("SEPA3 Transfer")
        verbose_name_plural = _("SEPA3 Transfers")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the SEPA3 Transfer.
        
        Returns:
            str: A formatted string with key transfer information
        """
        return f"{self.sender_name} → {self.recipient_name} | {self.amount} {self.currency}"
    
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


class TransferAttachment(models.Model):
    """
    Model for storing files attached to transfers.
    
    Allows attaching documents, receipts, or other files to transfers
    and tracking their metadata.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this attachment")
    )
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        help_text=_("Transfer this attachment belongs to")
    )
    sepa2_transfer = models.ForeignKey(
        SEPA2,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        help_text=_("SEPA2 transfer this attachment belongs to")
    )
    sepa3_transfer = models.ForeignKey(
        SEPA3,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        help_text=_("SEPA3 transfer this attachment belongs to")
    )
    file = models.FileField(
        upload_to='transfer_attachments/%Y/%m/%d/',
        help_text=_("The attached file")
    )
    filename = models.CharField(
        max_length=255,
        help_text=_("Original filename of the attachment")
    )
    file_type = models.CharField(
        max_length=50,
        help_text=_("MIME type of the file")
    )
    file_size = models.IntegerField(
        help_text=_("Size of the file in bytes")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the file was uploaded")
    )
    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        help_text=_("User who uploaded the file")
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description of the attachment")
    )
    
    class Meta:
        """
        Metadata for the TransferAttachment model.
        """
        verbose_name = _("Transfer Attachment")
        verbose_name_plural = _("Transfer Attachments")
        ordering = ['-uploaded_at']
    
    def __str__(self) -> str:
        """
        String representation of the attachment.
        
        Returns:
            str: A formatted string showing the filename and related transfer
        """
        transfer_id = None
        if self.transfer:
            transfer_id = self.transfer.id
        elif self.sepa2_transfer:
            transfer_id = self.sepa2_transfer.reference
        elif self.sepa3_transfer:
            transfer_id = self.sepa3_transfer.idempotency_key
            
        return f"{self.filename} ({transfer_id})"
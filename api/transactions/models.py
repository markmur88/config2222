"""
Models for the Transactions application.

This module defines database models for tracking financial transactions,
including standard transactions and SEPA transfers.
"""
import uuid
from typing import Any, Dict, Optional, Union

from django.db import models
from django.utils.translation import gettext_lazy as _

from api.accounts.models import Account
from api.core.choices import DIRECTION_CHOICES, STATUS_CHOICES, TRANSFER_TYPES, TYPE_STRATEGIES
from api.core.models import CoreModel, Debtor
from api.collection.models import Collection


class Transaction(CoreModel):
    """
    Model for standard financial transactions.
    
    Records details of money transfers between accounts, including
    source and destination information, amount, and status.
    """
    # Unique identifiers
    reference = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique reference for this transaction")
    )
    idempotency_key = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        help_text=_("Ensures uniqueness of transaction processing")
    )
    
    # Account relationships
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='transaction_set',
        help_text=_("Primary account for this transaction")
    )
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
        help_text=_("Local IBAN used for the transaction")
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Transaction amount")
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text=_("Currency code (e.g., EUR, USD)")
    )
    direction = models.CharField(
        max_length=10, 
        choices=DIRECTION_CHOICES,
        help_text=_("Whether the transaction is outgoing (debit) or incoming (credit)")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transaction")
    )
    
    # Dates
    request_date = models.DateTimeField(
        help_text=_("When the transaction was requested")
    )
    execution_date = models.DateTimeField(
        help_text=_("When the transaction was/will be executed")
    )
    accounting_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the transaction was recorded in accounting")
    )
    
    # Additional information
    counterparty_name = models.CharField(
        max_length=255,
        help_text=_("Name of the counterparty (recipient or sender)")
    )
    internal_note = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Internal notes about this transaction")
    )
    custom_id = models.CharField(
        max_length=256, 
        blank=True, 
        null=True,
        help_text=_("Custom identifier for this transaction")
    )
    custom_metadata = models.JSONField(
        blank=True, 
        null=True,
        help_text=_("Additional metadata in JSON format")
    )
    attachment_count = models.IntegerField(
        default=0,
        help_text=_("Number of files attached to this transaction")
    )
    
    class Meta:
        """
        Metadata for the Transaction model.
        """
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status']),
            models.Index(fields=['request_date']),
            models.Index(fields=['execution_date']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the Transaction.
        
        Returns:
            str: A formatted string showing source, destination, and amount
        """
        return f"{self.source_account} → {self.destination_account} | {self.amount} {self.currency}"
    
    def is_completed(self) -> bool:
        """
        Check if the transaction is completed.
        
        Returns:
            bool: True if the transaction is completed, False otherwise
        """
        return self.status in ['ACSC', 'ACCC']
    
    def is_pending(self) -> bool:
        """
        Check if the transaction is pending.
        
        Returns:
            bool: True if the transaction is pending, False otherwise
        """
        return self.status in ['PDNG', 'ACSP', 'ACWP']
    
    def is_failed(self) -> bool:
        """
        Check if the transaction has failed.
        
        Returns:
            bool: True if the transaction has failed, False otherwise
        """
        return self.status in ['RJCT', 'CANC']


class SEPA(CoreModel):
    """
    Model for SEPA (Single Euro Payments Area) transfers.
    
    Records details of standardized European bank transfers, including
    all required SEPA information and tracking data.
    """
    # Unique identifiers
    transaction_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Unique transaction identifier")
    )
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
    
    # Account relationship
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='transactions_sepa_set',
        help_text=_("Primary account for this transfer")
    )
    
    # Transfer details
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
    
    # Beneficiary information
    beneficiary_name = models.ForeignKey(
        Debtor, 
        on_delete=models.CASCADE,
        help_text=_("Recipient of the transfer")
    )
    
    # Additional details
    transfer_type = models.CharField(
        max_length=20, 
        choices=TRANSFER_TYPES, 
        null=True, 
        blank=True,
        help_text=_("Type of SEPA transfer (standard or instant)")
    )
    type_strategy = models.CharField(
        max_length=20, 
        choices=TYPE_STRATEGIES,
        help_text=_("Strategy for handling transfer type")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transfer")
    )
    direction = models.CharField(
        max_length=10, 
        choices=DIRECTION_CHOICES,
        help_text=_("Whether the transfer is outgoing (debit) or incoming (credit)")
    )
    failure_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text=_("Error code in case of failure")
    )
    message = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text=_("Status or error message")
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
        null=True, 
        blank=True,
        help_text=_("Date when the transfer is scheduled")
    )
    request_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the transfer was requested")
    )
    execution_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the transfer was/will be executed")
    )
    accounting_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When the transfer was recorded in accounting")
    )
    
    class Meta:
        """
        Metadata for the SEPA model.
        """
        verbose_name = _("SEPA Transfer")
        verbose_name_plural = _("SEPA Transfers")
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status']),
            models.Index(fields=['request_date']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the SEPA transfer.
        
        Returns:
            str: A formatted string showing transaction and idempotency IDs
        """
        return f"SEPA: {self.transaction_id} | {self.amount} {self.currency} | {self.beneficiary_name}"
    
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
    
    def is_failed(self) -> bool:
        """
        Check if the transfer has failed.
        
        Returns:
            bool: True if the transfer has failed, False otherwise
        """
        return self.status in ['RJCT', 'CANC']


class TransactionAttachment(models.Model):
    """
    Model for storing files attached to transactions.
    
    Allows attaching documents, receipts, or other files to transactions
    and tracking their metadata.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for this attachment")
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_("Transaction this attachment belongs to")
    )
    sepa_transaction = models.ForeignKey(
        SEPA,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        help_text=_("SEPA transfer this attachment belongs to")
    )
    file = models.FileField(
        upload_to='transaction_attachments/%Y/%m/%d/',
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
    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description of the attachment")
    )
    
    class Meta:
        """
        Metadata for the TransactionAttachment model.
        """
        verbose_name = _("Transaction Attachment")
        verbose_name_plural = _("Transaction Attachments")
        ordering = ['-uploaded_at']
    
    def __str__(self) -> str:
        """
        String representation of the attachment.
        
        Returns:
            str: A formatted string showing the filename and related transaction
        """
        transaction_id = self.transaction.id if self.transaction else self.sepa_transaction.transaction_id
        return f"{self.filename} ({transaction_id})"


class SEPA3(CoreModel):
    """
    Extended model for SEPA transfers with additional features.
    A more comprehensive SEPA transfer model that includes extra fields
    for regulatory compliance and additional business needs.
    """
    # Override the related_name for created_by
    # This assumes CoreModel has a created_by field that we need to override
    created_by = models.ForeignKey(
        'authentication.CustomUser',  # Adjust this import path if needed
        on_delete=models.CASCADE,
        related_name="created_transaction_sepa3_set",  # Changed related_name here
        help_text=_("User who created this transfer")
    )

    # Core payment information
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text=_("Transfer amount")
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text=_("Currency code (normally EUR for SEPA)")
    )
    payment_id = models.UUIDField(
        default=uuid.uuid4, 
        unique=True,
        help_text=_("Unique payment identifier")
    )
    purpose_code = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        help_text=_("ISO 20022 purpose code")
    )
    execution_date = models.DateField(
        help_text=_("Requested execution date")
    )
    
    # Debtor (sender) information
    debtor_name = models.CharField(
        max_length=140,
        help_text=_("Name of the sender")
    )
    debtor_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the sender")
    )
    debtor_bic = models.CharField(
        max_length=11,
        help_text=_("BIC of the sender's bank")
    )
    
    # Creditor (recipient) information
    creditor_name = models.CharField(
        max_length=140,
        help_text=_("Name of the recipient")
    )
    creditor_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the recipient")
    )
    creditor_bic = models.CharField(
        max_length=11,
        help_text=_("BIC of the recipient's bank")
    )
    
    # Payment details
    end_to_end_id = models.CharField(
        max_length=35, 
        default=uuid.uuid4,
        help_text=_("End-to-end identifier for tracing the payment")
    )
    remittance_info = models.CharField(
        max_length=140, 
        blank=True, 
        null=True,
        help_text=_("Payment reference information")
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PDNG',
        help_text=_("Current status of the transfer")
    )
    
    class Meta:
        """
        Metadata for the SEPA3 model.
        """
        verbose_name = _("Enhanced SEPA Transfer")
        verbose_name_plural = _("Enhanced SEPA Transfers")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['debtor_iban']),
            models.Index(fields=['creditor_iban']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the enhanced SEPA transfer.
        
        Returns:
            str: A formatted string showing core transfer details
        """
        return f"{self.debtor_name} → {self.creditor_name} | {self.amount} {self.currency}"
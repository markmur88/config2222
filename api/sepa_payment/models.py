"""
Models for the SEPA Payment application.

This module defines models for managing SEPA credit transfers, 
including transfer details, status history, and error tracking.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator
from decimal import Decimal
from typing import Dict, Any


class SepaCreditTransfer(models.Model):
    """
    Model representing a SEPA Credit Transfer.
    
    Stores the core information needed for processing SEPA transfers.
    """
    payment_id = models.CharField(
        max_length=50, 
        primary_key=True,
        help_text=_("Unique identifier for this payment")
    )
    auth_id = models.CharField(
        max_length=50,
        help_text=_("Authentication identifier for this payment")
    )
    transaction_status = models.CharField(
        max_length=10,
        help_text=_("Current status of the transaction")
    )
    purpose_code = models.CharField(
        max_length=4,
        help_text=_("Purpose code according to ISO 20022")
    )
    requested_execution_date = models.DateField(
        help_text=_("Date when the transfer should be executed")
    )
    
    # Debtor (sender) information
    debtor_name = models.CharField(
        max_length=140,
        help_text=_("Name of the debtor (sender)")
    )
    debtor_iban = models.CharField(
        max_length=34, 
        validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')],
        help_text=_("IBAN of the debtor account")
    )
    debtor_currency = models.CharField(
        max_length=3,
        help_text=_("Currency of the debtor account")
    )
    debtor_address_country = models.CharField(
        max_length=2,
        help_text=_("Country code of the debtor's address")
    )
    debtor_address_street = models.CharField(
        max_length=70,
        help_text=_("Street and building number of the debtor's address")
    )
    debtor_address_zip = models.CharField(
        max_length=70,
        help_text=_("Postal code and city of the debtor's address")
    )
    
    # Creditor (recipient) information
    creditor_name = models.CharField(
        max_length=70,
        help_text=_("Name of the creditor (recipient)")
    )
    creditor_iban = models.CharField(
        max_length=34, 
        validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')],
        help_text=_("IBAN of the creditor account")
    )
    creditor_currency = models.CharField(
        max_length=3,
        help_text=_("Currency of the creditor account")
    )
    creditor_address_country = models.CharField(
        max_length=2,
        help_text=_("Country code of the creditor's address")
    )
    creditor_address_street = models.CharField(
        max_length=70,
        help_text=_("Street and building number of the creditor's address")
    )
    creditor_address_zip = models.CharField(
        max_length=70,
        help_text=_("Postal code and city of the creditor's address")
    )
    creditor_agent_id = models.CharField(
        max_length=50,
        help_text=_("Financial institution identifier of the creditor agent")
    )
    
    # Payment information
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Amount of the payment")
    )
    end_to_end_id = models.CharField(
        max_length=35,
        help_text=_("End-to-end identifier for the payment")
    )
    instruction_id = models.CharField(
        max_length=35,
        help_text=_("Instruction identifier for the payment")
    )
    remittance_structured = models.CharField(
        max_length=140, 
        null=True, 
        blank=True,
        help_text=_("Structured remittance information")
    )
    remittance_unstructured = models.CharField(
        max_length=140, 
        null=True, 
        blank=True,
        help_text=_("Unstructured remittance information")
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this record was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When this record was last updated")
    )
    
    class Meta:
        """
        Metadata for the SepaCreditTransfer model.
        """
        verbose_name = _('SEPA Credit Transfer')
        verbose_name_plural = _('SEPA Credit Transfers')
        indexes = [
            models.Index(fields=['transaction_status']),
            models.Index(fields=['requested_execution_date']),
            models.Index(fields=['debtor_iban']),
            models.Index(fields=['creditor_iban']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the SEPA Credit Transfer.
        
        Returns:
            str: A string with payment ID
        """
        return f'SEPA Credit Transfer {self.payment_id}'
    
    @property
    def is_pending(self) -> bool:
        """
        Check if the transfer is pending.
        
        Returns:
            bool: True if status is 'PDNG', False otherwise
        """
        return self.transaction_status == 'PDNG'
    
    @property
    def is_completed(self) -> bool:
        """
        Check if the transfer is completed.
        
        Returns:
            bool: True if status is 'ACSC', False otherwise
        """
        return self.transaction_status == 'ACSC'
    
    @property
    def is_rejected(self) -> bool:
        """
        Check if the transfer is rejected.
        
        Returns:
            bool: True if status is 'RJCT', False otherwise
        """
        return self.transaction_status == 'RJCT'
    
    @property
    def full_debtor_address(self) -> str:
        """
        Get the full debtor address as a formatted string.
        
        Returns:
            str: Complete debtor address
        """
        return f"{self.debtor_address_street}, {self.debtor_address_zip}, {self.debtor_address_country}"
    
    @property
    def full_creditor_address(self) -> str:
        """
        Get the full creditor address as a formatted string.
        
        Returns:
            str: Complete creditor address
        """
        return f"{self.creditor_address_street}, {self.creditor_address_zip}, {self.creditor_address_country}"


class SepaCreditTransferStatus(models.Model):
    """
    Stores the status history of each SEPA transfer.
    
    This allows tracking the complete lifecycle of a payment.
    """
    STATUS_CHOICES = [
        ('RJCT', _('Rejected')),
        ('RCVD', _('Received')),
        ('ACCP', _('Accepted')),
        ('ACTC', _('Accepted Technical Validation')),
        ('ACSP', _('Accepted Settlement in Process')),
        ('ACSC', _('Accepted Settlement Completed')),
        ('ACWC', _('Accepted with Change')),
        ('ACWP', _('Accepted with Pending')),
        ('ACCC', _('Accepted Credit Check')),
        ('CANC', _('Cancelled')),
        ('PDNG', _('Pending')),
    ]
    
    payment = models.ForeignKey(
        SepaCreditTransfer, 
        on_delete=models.CASCADE, 
        related_name='status_history',
        help_text=_("The payment this status belongs to")
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES,
        help_text=_("Status code of the payment")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this status was recorded")
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Additional notes about this status change")
    )
    
    class Meta:
        """
        Metadata for the SepaCreditTransferStatus model.
        """
        verbose_name = _('SEPA Credit Transfer Status')
        verbose_name_plural = _('SEPA Credit Transfer Statuses')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the status history entry.
        
        Returns:
            str: A string with status and payment ID
        """
        return f'Status {self.status} for transfer {self.payment.payment_id}'


class SepaCreditTransferDetails(models.Model):
    """
    Stores a complete copy of the transfer details.
    
    Useful for audit and backup purposes.
    """
    payment = models.OneToOneField(
        SepaCreditTransfer, 
        on_delete=models.CASCADE, 
        related_name='details',
        help_text=_("The payment these details belong to")
    )
    auth_id = models.CharField(
        max_length=50,
        help_text=_("Authentication identifier for this payment")
    )
    transaction_status = models.CharField(
        max_length=10,
        help_text=_("Status of the transaction when these details were captured")
    )
    purpose_code = models.CharField(
        max_length=4,
        help_text=_("Purpose code according to ISO 20022")
    )
    requested_execution_date = models.DateField(
        help_text=_("Date when the transfer should be executed")
    )
    
    # Debtor (sender) information
    debtor_name = models.CharField(
        max_length=140,
        help_text=_("Name of the debtor (sender)")
    )
    debtor_iban = models.CharField(
        max_length=34, 
        validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')],
        help_text=_("IBAN of the debtor account")
    )
    debtor_currency = models.CharField(
        max_length=3,
        help_text=_("Currency of the debtor account")
    )
    
    # Creditor (recipient) information
    creditor_name = models.CharField(
        max_length=70,
        help_text=_("Name of the creditor (recipient)")
    )
    creditor_iban = models.CharField(
        max_length=34, 
        validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')],
        help_text=_("IBAN of the creditor account")
    )
    creditor_currency = models.CharField(
        max_length=3,
        help_text=_("Currency of the creditor account")
    )
    
    # Payment information
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Amount of the payment")
    )
    end_to_end_id = models.CharField(
        max_length=35,
        help_text=_("End-to-end identifier for the payment")
    )
    instruction_id = models.CharField(
        max_length=35,
        help_text=_("Instruction identifier for the payment")
    )
    remittance_structured = models.CharField(
        max_length=140, 
        null=True, 
        blank=True,
        help_text=_("Structured remittance information")
    )
    remittance_unstructured = models.CharField(
        max_length=140, 
        null=True, 
        blank=True,
        help_text=_("Unstructured remittance information")
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When these details were captured")
    )
    
    class Meta:
        """
        Metadata for the SepaCreditTransferDetails model.
        """
        verbose_name = _('SEPA Credit Transfer Details')
        verbose_name_plural = _('SEPA Credit Transfer Details')
    
    def __str__(self) -> str:
        """
        String representation of the transfer details.
        
        Returns:
            str: A string with payment ID
        """
        return f'Details for transfer {self.payment.payment_id}'


class SepaCreditTransferError(models.Model):
    """
    Records errors during the transfer process.
    
    Provides a detailed history of errors for troubleshooting and auditing.
    """
    # Error codes with descriptions
    ERROR_CODES = {
        2: _('Invalid value'),
        114: _('Cannot identify transaction'),
        121: _('Invalid OTP challenge response'),
        122: _('Invalid OTP'),
        127: _('Start date must precede end date'),
        131: _('Invalid value for sortBy'),
        132: _('Not supported'),
        138: _('Non-pushTAN challenge initiated'),
        139: _('PushTAN challenge initiated'),
        6500: _('Incorrect parameters'),
        6501: _('Invalid bank details'),
        6502: _('Only EUR currency is accepted'),
        6503: _('Missing or invalid parameters'),
        6505: _('Invalid execution date'),
        6507: _('Cancellation not allowed'),
        6509: _('Parameter does not match last Auth ID'),
        6510: _('Current status does not allow second factor update'),
        6511: _('Invalid execution date'),
        6515: _('Invalid source account type'),
        6516: _('Cancellation not allowed'),
        6517: _('Only EUR currency is accepted for creditor'),
        6518: _('Requested date cannot be a holiday or weekend'),
        6519: _('Execution date must not be more than 90 days in the future'),
        6520: _('Date format must be yyyy-MM-dd'),
        6521: _('Only EUR currency is accepted for debtor'),
        6523: _('No legal entity present for source IBAN'),
        6524: _('Maximum allowed limit for the day has been reached')
    }
    
    payment = models.ForeignKey(
        SepaCreditTransfer, 
        on_delete=models.CASCADE, 
        related_name='errors',
        help_text=_("The payment this error belongs to")
    )
    error_code = models.IntegerField(
        help_text=_("Error code from the payment processing system")
    )
    error_message = models.TextField(
        help_text=_("Detailed error message")
    )
    message_id = models.CharField(
        max_length=50,
        help_text=_("Message identifier associated with this error")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this error occurred")
    )
    
    class Meta:
        """
        Metadata for the SepaCreditTransferError model.
        """
        verbose_name = _('SEPA Credit Transfer Error')
        verbose_name_plural = _('SEPA Credit Transfer Errors')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['error_code']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the error.
        
        Returns:
            str: A string with error code and payment ID
        """
        return f'Error {self.error_code} for transfer {self.payment.payment_id}'
    
    @property
    def error_description(self) -> str:
        """
        Get a human-readable description of the error code.
        
        Returns:
            str: Description of the error code or a default message
        """
        return self.ERROR_CODES.get(self.error_code, _('Error description not found'))
"""
Models for the Sandbox application.

This module defines models for simulating banking operations in a sandbox
environment for testing and development purposes.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from api.core.choices import SANDBOX_STATUS_CHOICES, CURRENCY_CODES
from api.core.models import CoreModel


class IncomingCollection(CoreModel):
    """
    Model for simulating incoming collections in the sandbox environment.
    
    This model represents collections that would be received from external
    banking systems, allowing testing without actual bank interactions.
    """
    reference_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text=_("Bank reference identifier for this collection")
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_("Amount to be collected")
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CODES,
        default="EUR",
        help_text=_("Currency code (ISO 4217)")
    )
    sender_name = models.CharField(
        max_length=255,
        help_text=_("Name of the sending party")
    )
    sender_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the sending account")
    )
    recipient_iban = models.CharField(
        max_length=34,
        help_text=_("IBAN of the receiving account")
    )
    transaction_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Date and time when this collection was created")
    )
    status = models.CharField(
        max_length=20, 
        choices=SANDBOX_STATUS_CHOICES, 
        default="PENDING",
        help_text=_("Current status of the collection")
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Additional notes or comments about this collection")
    )
    
    class Meta:
        """
        Metadata for the IncomingCollection model.
        """
        verbose_name = _("Incoming Collection")
        verbose_name_plural = _("Incoming Collections")
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['reference_id']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_date']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the incoming collection.
        
        Returns:
            str: Reference ID, amount and currency
        """
        return f"{self.reference_id} - {self.amount} {self.currency}"
    
    def approve(self) -> bool:
        """
        Approve this collection and update its status.
        
        Returns:
            bool: True if the collection was approved successfully
        """
        if self.status != "PENDING":
            return False
            
        self.status = "COMPLETED"
        self.save(update_fields=['status'])
        return True
    
    def reject(self, reason: str = None) -> bool:
        """
        Reject this collection and update its status.
        
        Args:
            reason: The reason for rejection
            
        Returns:
            bool: True if the collection was rejected successfully
        """
        if self.status != "PENDING":
            return False
            
        self.status = "REJECTED"
        if reason:
            self.notes = reason
            self.save(update_fields=['status', 'notes'])
        else:
            self.save(update_fields=['status'])
        return True
    
    @property
    def is_pending(self) -> bool:
        """
        Check if the collection is pending.
        
        Returns:
            bool: True if status is PENDING, False otherwise
        """
        return self.status == "PENDING"
    
    @property
    def is_completed(self) -> bool:
        """
        Check if the collection is completed.
        
        Returns:
            bool: True if status is COMPLETED, False otherwise
        """
        return self.status == "COMPLETED"
    
    @property
    def is_rejected(self) -> bool:
        """
        Check if the collection is rejected.
        
        Returns:
            bool: True if status is REJECTED, False otherwise
        """
        return self.status == "REJECTED"


class SandboxBankAccount(CoreModel):
    """
    Model for simulating bank accounts in the sandbox environment.
    
    Provides a way to test bank account operations without using real accounts.
    """
    account_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text=_("Account number (can be an IBAN or other format)")
    )
    account_holder = models.CharField(
        max_length=255,
        help_text=_("Name of the account holder")
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        help_text=_("Current account balance")
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CODES,
        default="EUR",
        help_text=_("Currency code (ISO 4217)")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this account is active")
    )
    daily_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=10000.00,
        help_text=_("Maximum amount that can be transferred in a day")
    )
    
    class Meta:
        """
        Metadata for the SandboxBankAccount model.
        """
        verbose_name = _("Sandbox Bank Account")
        verbose_name_plural = _("Sandbox Bank Accounts")
        ordering = ['account_holder']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the bank account.
        
        Returns:
            str: Account holder name and account number
        """
        return f"{self.account_holder} - {self.account_number}"
    
    def deposit(self, amount: float) -> bool:
        """
        Deposit funds into this account.
        
        Args:
            amount: The amount to deposit
            
        Returns:
            bool: True if deposit was successful
            
        Raises:
            ValueError: If amount is negative
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
            
        self.balance += amount
        self.save(update_fields=['balance'])
        return True
    
    def withdraw(self, amount: float) -> bool:
        """
        Withdraw funds from this account.
        
        Args:
            amount: The amount to withdraw
            
        Returns:
            bool: True if withdrawal was successful
            
        Raises:
            ValueError: If amount is negative or exceeds balance
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        if self.balance < amount:
            raise ValueError("Insufficient funds")
            
        self.balance -= amount
        self.save(update_fields=['balance'])
        return True


class SandboxTransaction(CoreModel):
    """
    Model for simulating bank transactions in the sandbox environment.
    
    Allows recording and tracking test transactions between sandbox accounts.
    """
    transaction_id = models.CharField(
        max_length=100, 
        unique=True,
        help_text=_("Unique identifier for this transaction")
    )
    from_account = models.ForeignKey(
        SandboxBankAccount,
        on_delete=models.CASCADE,
        related_name='outgoing_transactions',
        help_text=_("Account from which funds are withdrawn")
    )
    to_account = models.ForeignKey(
        SandboxBankAccount,
        on_delete=models.CASCADE,
        related_name='incoming_transactions',
        help_text=_("Account to which funds are deposited")
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_("Transaction amount")
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CODES,
        default="EUR",
        help_text=_("Currency code (ISO 4217)")
    )
    status = models.CharField(
        max_length=20, 
        choices=SANDBOX_STATUS_CHOICES, 
        default="PENDING",
        help_text=_("Current status of the transaction")
    )
    description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_("Description or purpose of the transaction")
    )
    error_message = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Error message if the transaction failed")
    )
    
    class Meta:
        """
        Metadata for the SandboxTransaction model.
        """
        verbose_name = _("Sandbox Transaction")
        verbose_name_plural = _("Sandbox Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the transaction.
        
        Returns:
            str: Transaction ID, amount and currency
        """
        return f"{self.transaction_id} - {self.amount} {self.currency}"
    
    def process(self) -> bool:
        """
        Process this transaction by transferring funds between accounts.
        
        Returns:
            bool: True if the transaction was processed successfully
        """
        if self.status != "PENDING":
            return False
            
        try:
            # Ensure both accounts have the same currency
            if self.from_account.currency != self.to_account.currency:
                raise ValueError("Currency mismatch between accounts")
                
            # Check if from_account has sufficient funds
            if self.from_account.balance < self.amount:
                raise ValueError("Insufficient funds")
                
            # Withdraw from source account
            self.from_account.withdraw(self.amount)
            
            # Deposit to destination account
            self.to_account.deposit(self.amount)
            
            # Update transaction status
            self.status = "COMPLETED"
            self.save(update_fields=['status'])
            
            return True
            
        except Exception as e:
            self.status = "FAILED"
            self.error_message = str(e)
            self.save(update_fields=['status', 'error_message'])
            return False
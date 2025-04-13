"""
Data models for the Accounts application.

This module defines database models for account management,
including account details, balances, and related information.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from typing import Any, Optional

from api.core.choices import ACCOUNT_TYPES, ACCOUNT_STATUS, TYPE
from api.core.models import CoreModel, IBAN


class Account(CoreModel, models.Model):
    """
    Model representing a bank account.
    
    Stores account information including name, status, balance, and associated IBAN.
    Inherits timestamp and UUID fields from CoreModel.
    """
    name = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Unique name for the account"
    )
    status = models.CharField(
        max_length=50, 
        choices=ACCOUNT_STATUS, 
        default='active',
        help_text="Current status of the account"
    )
    balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Current balance of the account"
    )
    currency = models.CharField(
        max_length=3, 
        default="EUR",
        help_text="Currency of the account (3-letter code)"
    )
    iban = models.ForeignKey(
        IBAN, 
        on_delete=models.CASCADE, 
        null=False, 
        blank=False,
        help_text="Primary IBAN associated with this account"
    )
    type = models.CharField(
        max_length=30, 
        choices=ACCOUNT_TYPES, 
        default='current_account',
        help_text="Type of account (e.g., current, savings)"
    )
    is_main = models.CharField(
        max_length=8, 
        choices=TYPE, 
        default='main',
        help_text="Indicates if this is the main account"
    )
    
    def __str__(self) -> str:
        """
        String representation of the account.
        
        Returns:
            str: The name of the account
        """
        return f"{self.name}"
    
    def clean(self) -> None:
        """
        Validate the account data.
        
        Performs custom validation such as ensuring currency is valid
        and balance is appropriate.
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate currency is a 3-letter code
        if self.currency and len(self.currency) != 3:
            raise ValidationError({'currency': 'Currency must be a 3-letter code.'})
        
        # Add other validations as needed
        super().clean()
    
    def deposit(self, amount: float) -> None:
        """
        Add funds to the account.
        
        Args:
            amount: The amount to deposit
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("Cannot deposit a negative amount")
        
        self.balance += amount
        self.save(update_fields=['balance'])
    
    def withdraw(self, amount: float) -> None:
        """
        Remove funds from the account.
        
        Args:
            amount: The amount to withdraw
            
        Raises:
            ValueError: If amount is negative or exceeds balance
        """
        if amount < 0:
            raise ValueError("Cannot withdraw a negative amount")
        
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        
        self.balance -= amount
        self.save(update_fields=['balance'])
    
    class Meta:
        """
        Metadata for the Account model.
        
        Defines the verbose name, ordering, and other model-level attributes.
        """
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
        ]
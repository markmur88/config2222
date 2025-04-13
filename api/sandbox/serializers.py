"""
Serializers for the Sandbox application.

This module defines serializers for handling sandbox data in API requests
and responses, including simulated collections and transactions.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any

from api.sandbox.models import IncomingCollection, SandboxBankAccount, SandboxTransaction


class IncomingCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for IncomingCollection model instances.
    
    Handles conversion between IncomingCollection objects and JSON representations,
    including validation and error handling.
    """
    status_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    transaction_date = serializers.DateTimeField(read_only=True)
    
    class Meta:
        """
        Metadata for the IncomingCollectionSerializer.
        """
        model = IncomingCollection
        fields = [
            'id', 'reference_id', 'amount', 'currency', 
            'sender_name', 'sender_iban', 'recipient_iban',
            'transaction_date', 'status', 'status_display',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'transaction_date']
    
    def get_status_display(self, obj: IncomingCollection) -> str:
        """
        Get the human-readable display value for status.
        
        Args:
            obj: The IncomingCollection instance
            
        Returns:
            str: The display value for the status field
        """
        return obj.get_status_display()
    
    def validate_amount(self, value: float) -> float:
        """
        Validate that the amount is positive.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount
            
        Raises:
            serializers.ValidationError: If amount is not positive
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be positive."))
        return value
    
    def validate_sender_iban(self, value: str) -> str:
        """
        Validate the sender IBAN format.
        
        Args:
            value: The IBAN to validate
            
        Returns:
            str: The validated IBAN
            
        Raises:
            serializers.ValidationError: If IBAN format is invalid
        """
        # Remove spaces and convert to uppercase
        value = value.replace(' ', '').upper()
        
        # Basic validation - improve with a proper IBAN validation library
        if len(value) < 15 or len(value) > 34:
            raise serializers.ValidationError(_("Invalid IBAN length."))
        
        return value
    
    def validate_recipient_iban(self, value: str) -> str:
        """
        Validate the recipient IBAN format.
        
        Args:
            value: The IBAN to validate
            
        Returns:
            str: The validated IBAN
            
        Raises:
            serializers.ValidationError: If IBAN format is invalid
        """
        # Remove spaces and convert to uppercase
        value = value.replace(' ', '').upper()
        
        # Basic validation - improve with a proper IBAN validation library
        if len(value) < 15 or len(value) > 34:
            raise serializers.ValidationError(_("Invalid IBAN length."))
        
        return value


class IncomingCollectionApproveSerializer(serializers.Serializer):
    """
    Serializer for approving an incoming collection.
    """
    approve = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate approval data.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict[str, Any]: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        approve = data.get('approve')
        reason = data.get('reason')
        
        if not approve and not reason:
            raise serializers.ValidationError(
                {"reason": _("Reason is required when rejecting a collection.")}
            )
        
        return data


class SandboxBankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for SandboxBankAccount model instances.
    
    Handles conversion between SandboxBankAccount objects and JSON representations.
    """
    currency_display = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        """
        Metadata for the SandboxBankAccountSerializer.
        """
        model = SandboxBankAccount
        fields = [
            'id', 'account_number', 'account_holder', 'balance',
            'currency', 'currency_display', 'is_active', 'daily_limit',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_currency_display(self, obj: SandboxBankAccount) -> str:
        """
        Get the human-readable display value for currency.
        
        Args:
            obj: The SandboxBankAccount instance
            
        Returns:
            str: The display value for the currency field
        """
        return obj.get_currency_display()
    
    def validate_balance(self, value: float) -> float:
        """
        Validate that the balance is non-negative.
        
        Args:
            value: The balance value to validate
            
        Returns:
            float: The validated balance
            
        Raises:
            serializers.ValidationError: If balance is negative
        """
        if value < 0:
            raise serializers.ValidationError(_("Balance cannot be negative."))
        return value
    
    def validate_daily_limit(self, value: float) -> float:
        """
        Validate that the daily limit is positive.
        
        Args:
            value: The daily limit value to validate
            
        Returns:
            float: The validated daily limit
            
        Raises:
            serializers.ValidationError: If daily limit is not positive
        """
        if value <= 0:
            raise serializers.ValidationError(_("Daily limit must be positive."))
        return value


class SandboxTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for SandboxTransaction model instances.
    
    Handles conversion between SandboxTransaction objects and JSON representations.
    """
    status_display = serializers.SerializerMethodField()
    from_account_details = SandboxBankAccountSerializer(source='from_account', read_only=True)
    to_account_details = SandboxBankAccountSerializer(source='to_account', read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        """
        Metadata for the SandboxTransactionSerializer.
        """
        model = SandboxTransaction
        fields = [
            'id', 'transaction_id', 'from_account', 'from_account_details',
            'to_account', 'to_account_details', 'amount', 'currency',
            'status', 'status_display', 'description', 'error_message',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status', 'error_message']
    
    def get_status_display(self, obj: SandboxTransaction) -> str:
        """
        Get the human-readable display value for status.
        
        Args:
            obj: The SandboxTransaction instance
            
        Returns:
            str: The display value for the status field
        """
        return obj.get_status_display()
    
    def validate_amount(self, value: float) -> float:
        """
        Validate that the amount is positive.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount
            
        Raises:
            serializers.ValidationError: If amount is not positive
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be positive."))
        return value
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transaction data.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict[str, Any]: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check that from_account and to_account are different
        if data.get('from_account') == data.get('to_account'):
            raise serializers.ValidationError(
                _("Source and destination accounts must be different.")
            )
        
        # Check for currency match (if both accounts exist)
        from_account = data.get('from_account')
        to_account = data.get('to_account')
        
        if from_account and to_account and from_account.currency != to_account.currency:
            raise serializers.ValidationError(
                _("Source and destination accounts must have the same currency.")
            )
        
        return data
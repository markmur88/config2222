"""
Serializers for the Accounts application.

This module defines serializers for transforming Account models to/from
JSON representations for use in the REST API.
"""
from rest_framework import serializers
from typing import Dict, Any, List

from api.accounts.models import Account


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Account model instances.
    
    Handles conversion between Account models and JSON-compatible data structures,
    including validation and representation customization.
    """
    # Custom fields can be added here
    iban_display = serializers.CharField(source='iban.iban', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_main_display = serializers.CharField(source='get_is_main_display', read_only=True)
    
    class Meta:
        """
        Metadata for the AccountSerializer.
        
        Defines the model, fields, and validation rules.
        """
        model = Account
        fields = [
            'id', 'name', 'status', 'status_display', 'balance', 
            'currency', 'iban', 'iban_display', 'type', 'type_display', 
            'is_main', 'is_main_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_balance(self, value: float) -> float:
        """
        Validate the balance field.
        
        Args:
            value: The balance value to validate
            
        Returns:
            float: The validated balance value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Example validation - ensure balance isn't negative
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value
    
    def validate_currency(self, value: str) -> str:
        """
        Validate the currency field.
        
        Args:
            value: The currency code to validate
            
        Returns:
            str: The validated currency code
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Example validation - ensure currency is 3 letters
        if len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter code.")
        return value.upper()
    
    def to_representation(self, instance: Account) -> Dict[str, Any]:
        """
        Customize the output representation of an Account.
        
        Args:
            instance: The Account instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields or format values as needed
        representation['balance_formatted'] = f"{instance.balance} {instance.currency}"
        
        return representation


class AccountListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing Accounts.
    
    Used for list views where less detail is needed.
    """
    class Meta:
        """Metadata for the AccountListSerializer."""
        model = Account
        fields = ['id', 'name', 'status', 'balance', 'currency', 'type']


class AccountDetailSerializer(AccountSerializer):
    """
    Detailed serializer for Account instances.
    
    Extends the base AccountSerializer with additional detail fields
    for use in detailed views.
    """
    # Add additional fields for detailed view
    transactions = serializers.SerializerMethodField()
    
    class Meta(AccountSerializer.Meta):
        """Metadata for the AccountDetailSerializer."""
        fields = AccountSerializer.Meta.fields + ['transactions']
    
    def get_transactions(self, obj: Account) -> List[Dict[str, Any]]:
        """
        Get recent transactions for the account.
        
        Args:
            obj: The Account instance
            
        Returns:
            List[Dict[str, Any]]: List of recent transactions
        """
        # This is a placeholder - implement actual transaction fetching logic
        # based on your transaction model
        return []
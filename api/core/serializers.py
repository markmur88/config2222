"""
Serializers for the Core application.

This module defines base serializers and serializers for core models
that can be used throughout the application for API interactions.
"""
from typing import Dict, Any, List, Optional, Type

from django.db import models
from rest_framework import serializers

from api.core.models import CoreModel, Core2Model, IBAN, Debtor, TransactionStatus, Message, ErrorResponse


class CoreSerializer(serializers.Serializer):
    """
    Base serializer with common functionality.
    
    This is an abstract base serializer that provides common validation,
    error handling, and utility methods for other serializers.
    """
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform common validation for all serializers.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict[str, Any]: The validated data
        """
        # Add any common validation logic here
        return data
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """
        Perform necessary eager loading of data to avoid N+1 queries.
        
        This method can be overridden by subclasses to specify related
        fields that should be prefetched or selected.
        
        Args:
            queryset: The queryset to enhance
            
        Returns:
            QuerySet: The queryset with select_related/prefetch_related applied
        """
        return queryset


class CoreModelSerializer(CoreSerializer, serializers.ModelSerializer):
    """
    Base serializer for CoreModel instances.
    
    Provides common fields and functionality for serializers of models
    that inherit from CoreModel.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        """
        Metadata for the CoreModelSerializer.
        
        Note: This is an abstract serializer, so no model is specified.
        Subclasses should specify their own model.
        """
        fields = ['id', 'created_at', 'updated_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """
        Perform necessary eager loading of data to avoid N+1 queries.
        
        Args:
            queryset: The queryset to enhance
            
        Returns:
            QuerySet: The queryset with select_related applied
        """
        return queryset.select_related('created_by')


class IBANSerializer(CoreModelSerializer):
    """
    Serializer for IBAN model instances.
    
    Handles conversion between IBAN objects and JSON-compatible data structures.
    """
    status_display = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    
    class Meta:
        """
        Metadata for the IBANSerializer.
        """
        model = IBAN
        fields = CoreModelSerializer.Meta.fields + [
            'iban', 'bic', 'bank_name', 'status', 'status_display',
            'type', 'type_display', 'allow_collections', 'is_deleted'
        ]
        read_only_fields = CoreModelSerializer.Meta.read_only_fields + [
            'status_display', 'type_display'
        ]
    
    def get_status_display(self, obj: IBAN) -> str:
        """
        Get the human-readable display value for status.
        
        Args:
            obj: The IBAN instance
            
        Returns:
            str: The display value for the status field
        """
        return obj.get_status_display()
    
    def get_type_display(self, obj: IBAN) -> str:
        """
        Get the human-readable display value for type.
        
        Args:
            obj: The IBAN instance
            
        Returns:
            str: The display value for the type field
        """
        return obj.get_type_display()
    
    def validate_iban(self, value: str) -> str:
        """
        Validate the IBAN format.
        
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
            raise serializers.ValidationError("Invalid IBAN length")
        
        return value
    
    def validate_bic(self, value: str) -> str:
        """
        Validate the BIC format.
        
        Args:
            value: The BIC to validate
            
        Returns:
            str: The validated BIC
            
        Raises:
            serializers.ValidationError: If BIC format is invalid
        """
        # Remove spaces and convert to uppercase
        value = value.replace(' ', '').upper()
        
        # Basic validation
        if len(value) not in [8, 11]:
            raise serializers.ValidationError("BIC must be 8 or 11 characters")
        
        return value


class DebtorSerializer(CoreModelSerializer):
    """
    Serializer for Debtor model instances.
    
    Handles conversion between Debtor objects and JSON-compatible data structures.
    """
    iban_detail = IBANSerializer(source='iban', read_only=True)
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        """
        Metadata for the DebtorSerializer.
        """
        model = Debtor
        fields = CoreModelSerializer.Meta.fields + [
            'name', 'iban', 'iban_detail', 'street', 'building_number',
            'postal_code', 'city', 'country', 'full_address'
        ]
        read_only_fields = CoreModelSerializer.Meta.read_only_fields + ['full_address']
    
    def get_full_address(self, obj: Debtor) -> str:
        """
        Get the full address as a formatted string.
        
        Args:
            obj: The Debtor instance
            
        Returns:
            str: Complete address with all components
        """
        return obj.full_address
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """
        Perform necessary eager loading of data to avoid N+1 queries.
        
        Args:
            queryset: The queryset to enhance
            
        Returns:
            QuerySet: The queryset with select_related applied
        """
        return super().setup_eager_loading(queryset).select_related('iban')
    
    def validate_country(self, value: str) -> str:
        """
        Validate the country code.
        
        Args:
            value: The country code to validate
            
        Returns:
            str: The validated country code
            
        Raises:
            serializers.ValidationError: If country code format is invalid
        """
        # Convert to uppercase
        value = value.upper()
        
        # Basic validation
        if len(value) != 2:
            raise serializers.ValidationError("Country code must be 2 characters (ISO 3166-1 alpha-2)")
        
        return value


class TransactionStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for TransactionStatus model instances.
    
    Handles conversion between TransactionStatus objects and JSON-compatible data structures.
    """
    class Meta:
        """
        Metadata for the TransactionStatusSerializer.
        """
        model = TransactionStatus
        fields = ['id', 'transaction_status', 'description']


class ErrorResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for ErrorResponse model instances.
    
    Handles conversion between ErrorResponse objects and JSON-compatible data structures.
    """
    class Meta:
        """
        Metadata for the ErrorResponseSerializer.
        """
        model = ErrorResponse
        fields = ['messageId', 'code', 'message']


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model instances.
    
    Handles conversion between Message objects and JSON-compatible data structures.
    """
    class Meta:
        """
        Metadata for the MessageSerializer.
        """
        model = Message
        fields = ['message_id', 'code', 'message']
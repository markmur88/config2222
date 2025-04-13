"""
Serializers for the Transfers application.

This module defines serializers for transforming transfer models to/from
JSON representations for use in the REST API.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List

from api.transfers.models import Transfer, SepaTransaction, SEPA2, SEPA3, TransferAttachment
from api.authentication.serializers import UserSerializer


class TransferAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for transfer attachments.
    
    Handles conversion between TransferAttachment models and JSON-compatible data.
    """
    file_url = serializers.SerializerMethodField()
    uploaded_by_username = serializers.ReadOnlyField(source='uploaded_by.username')
    
    class Meta:
        """Metadata for the TransferAttachmentSerializer."""
        model = TransferAttachment
        fields = [
            'id', 'file', 'file_url', 'filename', 'file_type', 
            'file_size', 'uploaded_at', 'uploaded_by', 
            'uploaded_by_username', 'description'
        ]
        read_only_fields = ['id', 'file_url', 'file_size', 'uploaded_at', 'uploaded_by_username']
    
    def get_file_url(self, obj: TransferAttachment) -> str:
        """
        Get the URL for the attachment file.
        
        Args:
            obj: The TransferAttachment instance
            
        Returns:
            str: The URL to access the file
        """
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return ''


class TransferListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing transfers.
    
    Used for list views where less detail is needed.
    """
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the TransferListSerializer."""
        model = Transfer
        fields = [
            'id', 'reference', 'source_account', 'destination_account',
            'amount', 'currency', 'status', 'status_display',
            'scheduled_date', 'created_at'
        ]
    
    def get_status_display(self, obj: Transfer) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The Transfer instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)


class TransferSerializer(serializers.ModelSerializer):
    """
    Serializer for Transfer model instances.
    
    Handles conversion between Transfer models and JSON-compatible data,
    including relationship handling and custom fields.
    """
    status_display = serializers.SerializerMethodField()
    attachments = TransferAttachmentSerializer(many=True, read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    
    class Meta:
        """Metadata for the TransferSerializer."""
        model = Transfer
        fields = [
            'id', 'reference', 'idempotency_key', 'source_account', 
            'destination_account', 'amount', 'currency', 'local_iban',
            'account', 'beneficiary_iban', 'transfer_type', 'type_strategy',
            'status', 'status_display', 'failure_code', 'scheduled_date',
            'message', 'end_to_end_id', 'internal_note', 'custom_id',
            'custom_metadata', 'created_at', 'attachments',
            'is_completed', 'is_pending'
        ]
        read_only_fields = [
            'id', 'reference', 'status_display', 'created_at',
            'is_completed', 'is_pending'
        ]
    
    def get_status_display(self, obj: Transfer) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The Transfer instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)
    
    def validate_amount(self, value: float) -> float:
        """
        Validate the amount field.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value
    
    def to_representation(self, instance: Transfer) -> Dict[str, Any]:
        """
        Customize the output representation of a Transfer.
        
        Args:
            instance: The Transfer instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields
        representation['amount_formatted'] = f"{instance.amount} {instance.currency}"
        
        return representation


class SepaTransactionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing SEPA transactions.
    
    Used for list views where less detail is needed.
    """
    class Meta:
        """Metadata for the SepaTransactionListSerializer."""
        model = SepaTransaction
        fields = [
            'transaction_id', 'sender_iban', 'recipient_name',
            'recipient_iban', 'amount', 'currency', 'status',
            'created_at'
        ]


class SepaTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for SepaTransaction model instances.
    
    Handles conversion between SepaTransaction models and JSON-compatible data.
    """
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the SepaTransactionSerializer."""
        model = SepaTransaction
        fields = [
            'transaction_id', 'sender_iban', 'recipient_iban',
            'recipient_name', 'amount', 'currency', 'status',
            'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status_display']
    
    def get_status_display(self, obj: SepaTransaction) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SepaTransaction instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)
    
    def validate_amount(self, value: float) -> float:
        """
        Validate the amount field.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value


class SEPA2ListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing SEPA2 transfers.
    
    Used for list views where less detail is needed.
    """
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the SEPA2ListSerializer."""
        model = SEPA2
        fields = [
            'reference', 'account_name', 'beneficiary_name',
            'amount', 'currency', 'status', 'status_display',
            'scheduled_date', 'request_date', 'created_by_username'
        ]
    
    def get_status_display(self, obj: SEPA2) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA2 instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)


class SEPA2Serializer(serializers.ModelSerializer):
    """
    Serializer for SEPA2 transfer model instances.
    
    Handles conversion between SEPA2 models and JSON-compatible data,
    including relationship handling and custom fields.
    """
    created_by_details = UserSerializer(source='created_by', read_only=True)
    status_display = serializers.SerializerMethodField()
    attachments = TransferAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        """Metadata for the SEPA2Serializer."""
        model = SEPA2
        fields = [
            'id', 'reference', 'idempotency_key', 'custom_id', 'end_to_end_id',
            'account_name', 'account_iban', 'account_bic', 'account_bank',
            'amount', 'currency', 'beneficiary_name', 'beneficiary_iban',
            'beneficiary_bic', 'beneficiary_bank', 'status', 'status_display',
            'purpose_code', 'internal_note', 'failure_code', 'message',
            'custom_metadata', 'scheduled_date', 'request_date',
            'execution_date', 'accounting_date', 'created_by',
            'created_by_details', 'attachments'
        ]
        read_only_fields = [
            'id', 'reference', 'idempotency_key', 'custom_id', 'end_to_end_id',
            'request_date', 'created_by_details', 'status_display'
        ]
    
    def get_status_display(self, obj: SEPA2) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA2 instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)
    
    def validate_amount(self, value: float) -> float:
        """
        Validate the amount field.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value
    
    def to_representation(self, instance: SEPA2) -> Dict[str, Any]:
        """
        Customize the output representation of a SEPA2 transfer.
        
        Args:
            instance: The SEPA2 instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields
        representation['amount_formatted'] = f"{instance.amount} {instance.currency}"
        
        return representation


class SEPA3ListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing SEPA3 transfers.
    
    Used for list views where less detail is needed.
    """
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the SEPA3ListSerializer."""
        model = SEPA3
        fields = [
            'idempotency_key', 'sender_name', 'recipient_name',
            'amount', 'currency', 'status', 'status_display',
            'execution_date', 'created_at', 'created_by_username'
        ]
    
    def get_status_display(self, obj: SEPA3) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA3 instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)


class SEPA3Serializer(serializers.ModelSerializer):
    """
    Serializer for SEPA3 transfer model instances.
    
    Handles conversion between SEPA3 models and JSON-compatible data,
    including relationship handling and custom fields.
    """
    created_by_details = UserSerializer(source='created_by', read_only=True)
    status_display = serializers.SerializerMethodField()
    attachments = TransferAttachmentSerializer(source='attachments', many=True, read_only=True)
    
    class Meta:
        """Metadata for the SEPA3Serializer."""
        model = SEPA3
        fields = [
            'id', 'idempotency_key', 'sender_name', 'sender_iban', 
            'sender_bic', 'sender_bank', 'recipient_name', 'recipient_iban', 
            'recipient_bic', 'recipient_bank', 'amount', 'currency', 
            'status', 'status_display', 'execution_date', 'reference', 
            'unstructured_remittance_info', 'created_at', 'updated_at',
            'created_by', 'created_by_details', 'attachments'
        ]
        read_only_fields = [
            'id', 'idempotency_key', 'created_at', 'updated_at', 
            'created_by_details', 'status_display'
        ]
    
    def get_status_display(self, obj: SEPA3) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA3 instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)
    
    def validate_amount(self, value: float) -> float:
        """
        Validate the amount field.
        
        Args:
            value: The amount value to validate
            
        Returns:
            float: The validated amount value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value
    
    def to_representation(self, instance: SEPA3) -> Dict[str, Any]:
        """
        Customize the output representation of a SEPA3 transfer.
        
        Args:
            instance: The SEPA3 instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields
        representation['amount_formatted'] = f"{instance.amount} {instance.currency}"
        
        return representation
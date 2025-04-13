"""
Serializers for the Transactions application.

This module defines serializers for transforming transaction models to/from
JSON representations for use in the REST API.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List

from api.transactions.models import Transaction, SEPA, TransactionAttachment, SEPA3
from api.accounts.serializers import AccountSerializer
from api.core.serializers import DebtorSerializer


class TransactionAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction attachments.
    
    Handles conversion between TransactionAttachment models and JSON-compatible data.
    """
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the TransactionAttachmentSerializer."""
        model = TransactionAttachment
        fields = [
            'id', 'file', 'file_url', 'filename', 'file_type', 
            'file_size', 'uploaded_at', 'description'
        ]
        read_only_fields = ['id', 'file_url', 'file_size', 'uploaded_at']
    
    def get_file_url(self, obj: TransactionAttachment) -> str:
        """
        Get the URL for the attachment file.
        
        Args:
            obj: The TransactionAttachment instance
            
        Returns:
            str: The URL to access the file
        """
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return ''


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing transactions.
    
    Used for list views where less detail is needed.
    """
    account_name = serializers.ReadOnlyField(source='account.name')
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the TransactionListSerializer."""
        model = Transaction
        fields = [
            'id', 'reference', 'source_account', 'destination_account',
            'amount', 'currency', 'direction', 'status', 'status_display',
            'request_date', 'execution_date', 'counterparty_name',
            'account_name'
        ]
    
    def get_status_display(self, obj: Transaction) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The Transaction instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model instances.
    
    Handles conversion between Transaction models and JSON-compatible data,
    including relationship handling and custom fields.
    """
    account_details = AccountSerializer(source='account', read_only=True)
    status_display = serializers.SerializerMethodField()
    attachments = TransactionAttachmentSerializer(many=True, read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    
    class Meta:
        """Metadata for the TransactionSerializer."""
        model = Transaction
        fields = [
            'id', 'reference', 'idempotency_key', 'account', 'account_details',
            'source_account', 'destination_account', 'amount', 'currency',
            'local_iban', 'direction', 'status', 'status_display',
            'request_date', 'execution_date', 'accounting_date',
            'counterparty_name', 'internal_note', 'custom_id',
            'custom_metadata', 'attachment_count', 'attachments',
            'created_at', 'updated_at', 'created_by',
            'is_completed', 'is_pending', 'is_failed'
        ]
        read_only_fields = [
            'id', 'reference', 'idempotency_key', 'created_at', 
            'updated_at', 'created_by', 'status_display',
            'is_completed', 'is_pending', 'is_failed'
        ]
    
    def get_status_display(self, obj: Transaction) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The Transaction instance
            
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
    
    def to_representation(self, instance: Transaction) -> Dict[str, Any]:
        """
        Customize the output representation of a Transaction.
        
        Args:
            instance: The Transaction instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields
        representation['amount_formatted'] = f"{instance.amount} {instance.currency}"
        
        return representation


class SEPAListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing SEPA transfers.
    
    Used for list views where less detail is needed.
    """
    account_name = serializers.ReadOnlyField(source='account.name')
    beneficiary_name_display = serializers.ReadOnlyField(source='beneficiary_name.name')
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the SEPAListSerializer."""
        model = SEPA
        fields = [
            'transaction_id', 'reference', 'account_name', 'amount', 'currency',
            'beneficiary_name_display', 'status', 'status_display',
            'request_date', 'scheduled_date', 'execution_date'
        ]
    
    def get_status_display(self, obj: SEPA) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)


class SEPASerializer(serializers.ModelSerializer):
    """
    Serializer for SEPA transfer model instances.
    
    Handles conversion between SEPA models and JSON-compatible data,
    including relationship handling and custom fields.
    """
    account_details = AccountSerializer(source='account', read_only=True)
    beneficiary_details = DebtorSerializer(source='beneficiary_name', read_only=True)
    status_display = serializers.SerializerMethodField()
    transfer_type_display = serializers.SerializerMethodField()
    type_strategy_display = serializers.SerializerMethodField()
    direction_display = serializers.SerializerMethodField()
    attachments = TransactionAttachmentSerializer(source='attachments', many=True, read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    
    class Meta:
        """Metadata for the SEPASerializer."""
        model = SEPA
        fields = [
            'transaction_id', 'reference', 'idempotency_key', 'custom_id', 'end_to_end_id',
            'account', 'account_details', 'amount', 'currency',
            'beneficiary_name', 'beneficiary_details', 'transfer_type', 'transfer_type_display',
            'type_strategy', 'type_strategy_display', 'status', 'status_display',
            'direction', 'direction_display', 'failure_code', 'message',
            'internal_note', 'custom_metadata', 'scheduled_date',
            'request_date', 'execution_date', 'accounting_date',
            'created_at', 'updated_at', 'created_by', 'attachments',
            'is_completed', 'is_pending', 'is_failed'
        ]
        read_only_fields = [
            'transaction_id', 'reference', 'idempotency_key', 'custom_id', 'end_to_end_id',
            'created_at', 'updated_at', 'created_by', 'request_date',
            'status_display', 'transfer_type_display', 'type_strategy_display', 'direction_display',
            'is_completed', 'is_pending', 'is_failed'
        ]
    
    def get_status_display(self, obj: SEPA) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The SEPA instance
            
        Returns:
            str: Human-readable status
        """
        return dict(obj._meta.model._meta.get_field('status').choices).get(obj.status, obj.status)
    
    def get_transfer_type_display(self, obj: SEPA) -> str:
        """
        Get the human-readable transfer type display.
        
        Args:
            obj: The SEPA instance
            
        Returns:
            str: Human-readable transfer type
        """
        if not obj.transfer_type:
            return ''
        return dict(obj._meta.model._meta.get_field('transfer_type').choices).get(obj.transfer_type, obj.transfer_type)
    
    def get_type_strategy_display(self, obj: SEPA) -> str:
        """
        Get the human-readable type strategy display.
        
        Args:
            obj: The SEPA instance
            
        Returns:
            str: Human-readable type strategy
        """
        return dict(obj._meta.model._meta.get_field('type_strategy').choices).get(obj.type_strategy, obj.type_strategy)
    
    def get_direction_display(self, obj: SEPA) -> str:
        """
        Get the human-readable direction display.
        
        Args:
            obj: The SEPA instance
            
        Returns:
            str: Human-readable direction
        """
        return dict(obj._meta.model._meta.get_field('direction').choices).get(obj.direction, obj.direction)
    
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
    
    def to_representation(self, instance: SEPA) -> Dict[str, Any]:
        """
        Customize the output representation of a SEPA transfer.
        
        Args:
            instance: The SEPA instance to represent
            
        Returns:
            Dict[str, Any]: The customized representation
        """
        representation = super().to_representation(instance)
        
        # Add calculated fields
        representation['amount_formatted'] = f"{instance.amount} {instance.currency}"
        
        return representation


class SEPA3Serializer(serializers.ModelSerializer):
    """
    Serializer for enhanced SEPA transfer model instances.
    
    Handles conversion between SEPA3 models and JSON-compatible data.
    """
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        """Metadata for the SEPA3Serializer."""
        model = SEPA3
        fields = [
            'id', 'payment_id', 'purpose_code', 'amount', 'currency',
            'debtor_name', 'debtor_iban', 'debtor_bic',
            'creditor_name', 'creditor_iban', 'creditor_bic',
            'end_to_end_id', 'remittance_info', 'status', 'status_display',
            'execution_date', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = [
            'id', 'payment_id', 'created_at', 'updated_at', 'created_by',
            'status_display'
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
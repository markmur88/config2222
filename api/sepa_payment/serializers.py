"""
Serializers for the SEPA Payment application.

This module defines serializers for transforming SEPA payment models to/from
JSON representations for use in the REST API.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any

from api.sepa_payment.models import (
    SepaCreditTransfer, 
    SepaCreditTransferStatus,
    SepaCreditTransferDetails,
    SepaCreditTransferError
)


class SepaCreditTransferStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for SEPA credit transfer status history entries.
    """
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SepaCreditTransferStatus
        fields = [
            'status', 
            'status_display',
            'timestamp', 
            'notes'
        ]
        read_only_fields = ['timestamp']
    
    def get_status_display(self, obj: SepaCreditTransferStatus) -> str:
        """
        Get the human-readable status display.
        
        Args:
            obj: The status object
            
        Returns:
            str: Human-readable status
        """
        return dict(SepaCreditTransferStatus.STATUS_CHOICES).get(obj.status, obj.status)


class SepaCreditTransferErrorSerializer(serializers.ModelSerializer):
    """
    Serializer for SEPA credit transfer error entries.
    """
    error_description = serializers.ReadOnlyField()
    
    class Meta:
        model = SepaCreditTransferError
        fields = [
            'error_code',
            'error_message',
            'message_id',
            'timestamp',
            'error_description'
        ]
        read_only_fields = ['timestamp', 'error_description']


class SepaCreditTransferDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for SEPA credit transfer details.
    """
    class Meta:
        model = SepaCreditTransferDetails
        exclude = ['id', 'payment']
        read_only_fields = ['created_at']


class SepaCreditTransferSerializer(serializers.ModelSerializer):
    """
    Serializer for SEPA credit transfers.
    
    Handles conversion between SepaCreditTransfer models and JSON-compatible data.
    """
    status_history = SepaCreditTransferStatusSerializer(many=True, read_only=True)
    errors = SepaCreditTransferErrorSerializer(many=True, read_only=True)
    details = SepaCreditTransferDetailsSerializer(read_only=True)
    is_pending = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    is_rejected = serializers.ReadOnlyField()
    full_debtor_address = serializers.ReadOnlyField()
    full_creditor_address = serializers.ReadOnlyField()
    
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'payment_id',
            'auth_id',
            'transaction_status',
            'purpose_code',
            'requested_execution_date',
            'debtor_name',
            'debtor_iban',
            'debtor_currency',
            'debtor_address_country',
            'debtor_address_street',
            'debtor_address_zip',
            'creditor_name',
            'creditor_iban',
            'creditor_currency',
            'creditor_address_country',
            'creditor_address_street',
            'creditor_address_zip',
            'creditor_agent_id',
            'amount',
            'end_to_end_id',
            'instruction_id',
            'remittance_structured',
            'remittance_unstructured',
            'created_at',
            'updated_at',
            'status_history',
            'errors',
            'details',
            'is_pending',
            'is_completed',
            'is_rejected',
            'full_debtor_address',
            'full_creditor_address'
        ]
        read_only_fields = [
            'payment_id',
            'created_at',
            'updated_at',
            'status_history',
            'errors',
            'details'
        ]
    
    def validate_amount(self, value):
        """
        Validate that the amount is positive.
        
        Args:
            value: The amount value to validate
            
        Returns:
            Decimal: The validated amount
            
        Raises:
            serializers.ValidationError: If amount is not positive
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value
    
    def validate(self, data):
        """
        Perform cross-field validation.
        
        Args:
            data: The validated data
            
        Returns:
            dict: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check that currencies match if both provided
        if ('debtor_currency' in data and 'creditor_currency' in data and
                data['debtor_currency'] != 'EUR' and data['creditor_currency'] != 'EUR'):
            raise serializers.ValidationError(_("At least one currency must be EUR for SEPA transfers"))
        
        return data


class SepaCreditTransferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating SEPA credit transfers.
    
    Simplified version of SepaCreditTransferSerializer with only the fields
    needed for creating a new transfer.
    """
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'auth_id',
            'purpose_code',
            'requested_execution_date',
            'debtor_name',
            'debtor_iban',
            'debtor_currency',
            'debtor_address_country',
            'debtor_address_street',
            'debtor_address_zip',
            'creditor_name',
            'creditor_iban',
            'creditor_currency',
            'creditor_address_country',
            'creditor_address_street',
            'creditor_address_zip',
            'creditor_agent_id',
            'amount',
            'end_to_end_id',
            'instruction_id',
            'remittance_structured',
            'remittance_unstructured',
        ]
    
    def validate_amount(self, value):
        """
        Validate that the amount is positive.
        
        Args:
            value: The amount value to validate
            
        Returns:
            Decimal: The validated amount
            
        Raises:
            serializers.ValidationError: If amount is not positive
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero"))
        return value


class SepaCreditTransferStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating the status of a SEPA credit transfer.
    """
    status = serializers.ChoiceField(
        choices=[choice[0] for choice in SepaCreditTransferStatus.STATUS_CHOICES],
        help_text=_("New status for the transfer")
    )
    notes = serializers.CharField(
        required=False,
        help_text=_("Optional notes about this status change")
    )
    
    def validate_status(self, value):
        """
        Validate the status code.
        
        Args:
            value: The status code to validate
            
        Returns:
            str: The validated status code
        """
        valid_statuses = dict(SepaCreditTransferStatus.STATUS_CHOICES)
        if value not in valid_statuses:
            raise serializers.ValidationError(_("Invalid status code"))
        return value
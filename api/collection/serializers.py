"""
Serializers for the Collection application.

This module defines serializers for transforming collection and mandate models
to and from JSON representations for use in the REST API.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List

from api.collection.models import Mandate, Collection


class MandateSerializer(serializers.ModelSerializer):
    """
    Serializer for Mandate model instances.
    
    Handles conversion between Mandate objects and JSON representations,
    including validation and relationship handling.
    """
    # Add read-only fields
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Add derived field for number of collections
    collection_count = serializers.SerializerMethodField()
    
    class Meta:
        """
        Metadata for the MandateSerializer.
        """
        model = Mandate
        fields = [
            'id', 'reference', 'scheme', 'debtor_name', 'debtor_iban',
            'signature_date', 'contract_reference', 'is_active',
            'created_at', 'updated_at', 'collection_count'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']
    
    def get_collection_count(self, obj: Mandate) -> int:
        """
        Get the number of collections associated with this mandate.
        
        Args:
            obj: The Mandate instance
            
        Returns:
            int: The count of associated collections
        """
        return obj.collections.count()
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform custom validation on the mandate data.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict[str, Any]: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Example validation: Ensure debtor_name and debtor_iban are for the same debtor
        debtor_name = data.get('debtor_name')
        debtor_iban = data.get('debtor_iban')
        
        if debtor_name and debtor_iban and debtor_name.id != debtor_iban.id:
            raise serializers.ValidationError({
                'debtor_iban': _("Debtor name and IBAN must belong to the same debtor.")
            })
        
        return data


class MandateListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing Mandates.
    
    Used for list views where less detail is needed.
    """
    debtor_name = serializers.StringRelatedField()
    
    class Meta:
        """
        Metadata for the MandateListSerializer.
        """
        model = Mandate
        fields = ['id', 'reference', 'scheme', 'debtor_name', 'is_active', 'signature_date']


class MandateDetailSerializer(MandateSerializer):
    """
    Detailed serializer for Mandate instances.
    
    Includes collections associated with the mandate.
    """
    collections = serializers.SerializerMethodField()
    
    class Meta(MandateSerializer.Meta):
        """
        Metadata for the MandateDetailSerializer.
        """
        fields = MandateSerializer.Meta.fields + ['collections']
    
    def get_collections(self, obj: Mandate) -> List[Dict[str, Any]]:
        """
        Get the collections associated with this mandate.
        
        Args:
            obj: The Mandate instance
            
        Returns:
            List[Dict[str, Any]]: List of simplified collection data
        """
        # Use a simple representation to avoid circular references
        collections = obj.collections.all()
        return [{
            'id': str(collection.id),
            'scheduled_date': collection.scheduled_date,
            'amount': collection.amount,
            'status': collection.status
        } for collection in collections]


class CollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for Collection model instances.
    
    Handles conversion between Collection objects and JSON representations,
    including validation and relationship handling.
    """
    # Add read-only fields
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Add derived fields for better representation
    debtor_name = serializers.SerializerMethodField()
    debtor_iban = serializers.SerializerMethodField()
    
    class Meta:
        """
        Metadata for the CollectionSerializer.
        """
        model = Collection
        fields = [
            'id', 'mandate', 'scheduled_date', 'amount', 'local_iban',
            'status', 'message', 'end_to_end_id', 'internal_note',
            'custom_id', 'custom_metadata', 'created_at', 'updated_at',
            'debtor_name', 'debtor_iban'
        ]
        read_only_fields = ['id', 'end_to_end_id', 'custom_id', 'created_at', 'updated_at']
    
    def get_debtor_name(self, obj: Collection) -> str:
        """
        Get the debtor name from the associated mandate.
        
        Args:
            obj: The Collection instance
            
        Returns:
            str: The name of the debtor
        """
        return str(obj.mandate.debtor_name)
    
    def get_debtor_iban(self, obj: Collection) -> str:
        """
        Get the debtor IBAN from the associated mandate.
        
        Args:
            obj: The Collection instance
            
        Returns:
            str: The IBAN of the debtor's account
        """
        return str(obj.mandate.debtor_iban)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform custom validation on the collection data.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict[str, Any]: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Validate that the mandate is active
        mandate = data.get('mandate')
        if mandate and not mandate.is_active:
            raise serializers.ValidationError({
                'mandate': _("Cannot create a collection with an inactive mandate.")
            })
        
        # Add more custom validation as needed
        return data


class CollectionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing Collections.
    
    Used for list views where less detail is needed.
    """
    debtor_name = serializers.SerializerMethodField()
    mandate_reference = serializers.SerializerMethodField()
    
    class Meta:
        """
        Metadata for the CollectionListSerializer.
        """
        model = Collection
        fields = ['id', 'mandate_reference', 'debtor_name', 'scheduled_date', 'amount', 'status']
    
    def get_debtor_name(self, obj: Collection) -> str:
        """
        Get the debtor name from the associated mandate.
        
        Args:
            obj: The Collection instance
            
        Returns:
            str: The name of the debtor
        """
        return str(obj.mandate.debtor_name)
    
    def get_mandate_reference(self, obj: Collection) -> str:
        """
        Get the reference of the associated mandate.
        
        Args:
            obj: The Collection instance
            
        Returns:
            str: The mandate reference
        """
        return str(obj.mandate.reference)


class CollectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Collections.
    
    Provides specific validation for collection creation.
    """
    class Meta:
        """
        Metadata for the CollectionCreateSerializer.
        """
        model = Collection
        fields = [
            'mandate', 'scheduled_date', 'amount', 'local_iban',
            'message', 'internal_note', 'custom_metadata'
        ]
    
    def validate_amount(self, value):
        """
        Validate the amount field.
        
        Args:
            value: The amount value to validate
            
        Returns:
            Decimal: The validated amount
            
        Raises:
            serializers.ValidationError: If amount is invalid
        """
        if value <= 0:
            raise serializers.ValidationError(_("Amount must be greater than zero."))
        return value
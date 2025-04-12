from rest_framework import serializers
from api.transfers.models import Transfer, SepaTransaction, SEPA2, SEPA3

class SEPA3Serializer(serializers.ModelSerializer):
    class Meta:
        model = SEPA3
        fields = ["id", "idempotency_key", "sender_name", "sender_iban", "sender_bic", "sender_bank", "recipient_name", "recipient_iban", "recipient_bic", "recipient_bank", "amount", "currency", "status", "execution_date", "reference", "unstructured_remittance_info", "created_by"]
        
        
class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ["source_account", "destination_account", "amount", "currency"]
        
class SepaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SepaTransaction
        fields = '__all__'

class SEPA2Serializer(serializers.ModelSerializer):
    class Meta:
        model = SEPA2
        fields = ["account_name", "account_iban", "account_bic", "account_bank", "amount", "currency", "beneficiary_name", "beneficiary_iban", "beneficiary_bic", "beneficiary_bank", "status", "purpose_code", "internal_note", "scheduled_date", "accounting_date", "created_by", "idempotency_key", "id", "reference", "custom_id", "end_to_end_id"]
        
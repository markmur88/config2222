from rest_framework import serializers
from api.sct.models import (
    ErrorResponse, SepaCreditTransferRequest, SepaCreditTransferUpdateScaRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse
)


class SepaCreditTransferRequestSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.UUIDField(read_only=True)
    payment_id = serializers.UUIDField(read_only=True, help_text="Resource identification of the generated payment initiation resource ('Transaction-ID').")
    auth_id = serializers.UUIDField(read_only=True, help_text="Authentication Id used for update SCA status SEPA payment, valid for 5 minutes.")
    payment_identification_end_to_end_id = serializers.UUIDField(read_only=True)
    payment_identification_instruction_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = SepaCreditTransferRequest
        fields = [
            'instructed_amount', 'instructed_currency',
            'id', 'transaction_status','purpose_code', 'idempotency_key', 
            'payment_id', 'auth_id', 'requested_execution_date', 'transaction_status', 
            'debtor_name', 'debtor_adress_street_and_house_number',
            'debtor_adress_zip_code_and_city', 'debtor_adress_country', 'debtor_account_iban',
            'debtor_account_bic', 'debtor_account_currency',
            'payment_identification_end_to_end_id', 'payment_identification_instruction_id',
            'creditor_name', 'creditor_adress_street_and_house_number',
            'creditor_adress_zip_code_and_city', 'creditor_adress_country',
            'creditor_account_iban', 'creditor_account_bic',
            'creditor_account_currency', 'creditor_agent_financial_institution_id',
            'remittance_information_structured', 'remittance_information_unstructured',
        ]


class SepaCreditTransferUpdateScaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SepaCreditTransferUpdateScaRequest
        fields = ['action', 'auth_id']


class SepaCreditTransferResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SepaCreditTransferResponse
        fields = ['transaction_status', 'payment_id', 'auth_id']


class SepaCreditTransferDetailsResponseSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.UUIDField(read_only=True)
    payment_id = serializers.UUIDField(read_only=True)
    payment_identification_end_to_end_id = serializers.UUIDField(read_only=True)
    payment_identification_instruction_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = SepaCreditTransferDetailsResponse
        fields = [
            'id', 'transaction_status','purpose_code', 
            'payment_id', 'requested_execution_date', 'transaction_status', 
            'debtor_name', 'debtor_adress_street_and_house_number',
            'debtor_adress_zip_code_and_city', 'debtor_adress_country', 'debtor_account_iban',
            'debtor_account_bic', 'debtor_account_currency',
            'payment_identification_end_to_end_id', 'payment_identification_instruction_id',
            'instructed_amount_currency', 'instructed_amount_amount',
            'creditor_name', 'creditor_adress_street_and_house_number',
            'creditor_adress_zip_code_and_city', 'creditor_adress_country',
            'creditor_account_iban', 'creditor_account_bic',
            'creditor_account_currency', 'creditor_agent_financial_institution_id',
            'remittance_information_structured', 'remittance_information_unstructured',
        ]


class ErrorResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorResponse
        fields = ['code', 'message', 'message_id']

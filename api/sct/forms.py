from django import forms
from api.sct.models import (
    SepaCreditTransferRequest
)


class SepaCreditTransferRequestForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransferRequest
        fields = '__all__'
        widgets = {
            'transaction_status': forms.Select(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de DateInput a TextInput
            
            'debtor_name': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_street_and_house_number': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_zip_code_and_city': forms.Select(attrs={'class': 'form-control'}),
            'debtor_adress_country': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_iban': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_bic': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account_currency': forms.Select(attrs={'class': 'form-control'}),

            'payment_identification_end_to_end_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_identification_instruction_id': forms.TextInput(attrs={'class': 'form-control'}),
            
            'instructed_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'instructed_currency': forms.Select(attrs={'class': 'form-control'}),  # Corregido de TextInput a Select
            
            'creditor_name': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_street_and_house_number': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_zip_code_and_city': forms.Select(attrs={'class': 'form-control'}),
            'creditor_adress_country': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_iban': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_bic': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account_currency': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent_financial_institution_id': forms.Select(attrs={'class': 'form-control'}),

            'remittance_information_structured': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de Textarea a TextInput
            'remittance_information_unstructured': forms.TextInput(attrs={'class': 'form-control'}),  # Corregido de Textarea a TextInput

         
            'requested_execution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'idempotency_key': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_id': forms.TextInput(attrs={'class': 'form-control'}),
            'auth_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

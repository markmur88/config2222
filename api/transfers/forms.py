from django import forms
from api.transfers.models import SEPA2, Transfer, SepaTransaction, SEPA3

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = [
            'idempotency_key', 'source_account', 'destination_account', 'amount',
            'currency', 'local_iban', 'account', 'beneficiary_iban', 'transfer_type',
            'type_strategy', 'status', 'failure_code', 'scheduled_date', 'message',
            'end_to_end_id', 'internal_note', 'custom_id', 'custom_metadata'
        ]

class SepaTransactionForm(forms.ModelForm):
    class Meta:
        model = SepaTransaction
        fields = [
            'transaction_id', 'sender_iban', 'recipient_iban', 'recipient_name',
            'amount', 'currency', 'status'
        ]

class SepaTransferForm(forms.ModelForm):
    class Meta:
        model = SepaTransaction
        fields = [
            'transaction_id', 'sender_iban', 'recipient_iban', 'recipient_name',
            'amount', 'currency', 'status'
        ]

class SEPA2Form(forms.ModelForm):
    class Meta:
        model = SEPA2
        fields = [
            'account_name', 'account_iban', 'account_bic', 'account_bank', 'amount',
            'currency', 'beneficiary_name', 'beneficiary_iban', 'beneficiary_bic',
            'beneficiary_bank', 'status', 'purpose_code', 'internal_note'
        ]
        widgets = {
            'account_name': forms.Select(attrs={'class': 'form-control'}),
            'account_iban': forms.Select(attrs={'class': 'form-control'}),
            'account_bic': forms.Select(attrs={'class': 'form-control'}),
            'account_bank': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiary_name': forms.Select(attrs={'class': 'form-control'}),
            'beneficiary_iban': forms.Select(attrs={'class': 'form-control'}),
            'beneficiary_bic': forms.Select(attrs={'class': 'form-control'}),
            'beneficiary_bank': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),
            'internal_note': forms.TextInput(attrs={'class': 'form-control'})
        }

class SEPA3Form(forms.ModelForm):
    class Meta:
        model = SEPA3
        fields = [
            'sender_name', 'sender_iban', 'sender_bic', 'sender_bank',
            'recipient_name', 'recipient_iban', 'recipient_bic', 'recipient_bank',
            'amount', 'currency', 'status', 'reference',
            'unstructured_remittance_info', 'created_by'

        ]
        widgets = {
            'created_by': forms.Select(attrs={'class': 'form-control'}),
            'sender_name': forms.Select(attrs={'class': 'form-control'}),
            'sender_iban': forms.Select(attrs={'class': 'form-control'}),
            'sender_bic': forms.Select(attrs={'class': 'form-control'}),
            'sender_bank': forms.Select(attrs={'class': 'form-control'}),
            'recipient_name': forms.Select(attrs={'class': 'form-control'}),
            'recipient_iban': forms.Select(attrs={'class': 'form-control'}),
            'recipient_bic': forms.Select(attrs={'class': 'form-control'}),
            'recipient_bank': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'unstructured_remittance_info': forms.TextInput(attrs={'class': 'form-control'})

        }
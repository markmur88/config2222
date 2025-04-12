from django import forms
from api.transactions.models import Transaction, SEPA

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'source_account',
            'destination_account',
            'amount',
            'currency',
            'direction',
            'request_date',
            'execution_date',
            'counterparty_name',
            'internal_note',
        ]
        widgets = {
            'request_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'execution_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class SEPAForm(forms.ModelForm):
    class Meta:
        model = SEPA
        fields = '__all__'
        widgets = {
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'beneficiary_name': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'transfer_type': forms.Select(attrs={'class': 'form-control'}),
            'type_strategy': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'direction': forms.Select(attrs={'class': 'form-control'}),
            #'failure_code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            #'message': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            #'internal_note': forms.TextInput(attrs={'class': 'form-control'}),
            #'custom_metadata': forms.TextInput(attrs={'class': 'form-control'}),

        }

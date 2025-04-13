"""
Forms for the Transfers application.

This module defines form classes for handling transfer-related data,
including different types of transfers and SEPA transactions.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from api.transfers.models import SEPA2, Transfer, SepaTransaction, SEPA3


class TransferForm(forms.ModelForm):
    """
    Form for creating and editing Transfer instances.
    
    Provides fields for basic transfer details, including accounts,
    amounts, and status information.
    """
    class Meta:
        """
        Metadata for the TransferForm.
        """
        model = Transfer
        fields = [
            'idempotency_key', 'source_account', 'destination_account', 
            'amount', 'currency', 'local_iban', 'account', 
            'beneficiary_iban', 'transfer_type', 'type_strategy', 
            'status', 'failure_code', 'scheduled_date', 'message',
            'end_to_end_id', 'internal_note', 'custom_id', 'custom_metadata'
        ]
        widgets = {
            'idempotency_key': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'source_account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'destination_account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'local_iban': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary_iban': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'transfer_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'type_strategy': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'failure_code': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'message': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'end_to_end_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'internal_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'custom_id': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'custom_metadata': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        help_texts = {
            'amount': _('Transfer amount (positive number)'),
            'currency': _('Currency for the transfer'),
            'scheduled_date': _('When the transfer should be executed'),
            'internal_note': _('Notes for internal use only'),
            'custom_metadata': _('Additional JSON metadata for this transfer'),
        }
        labels = {
            'idempotency_key': _('Idempotency Key'),
            'source_account': _('Source Account'),
            'destination_account': _('Destination Account'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'local_iban': _('Local IBAN'),
            'account': _('Account'),
            'beneficiary_iban': _('Beneficiary IBAN'),
            'transfer_type': _('Transfer Type'),
            'type_strategy': _('Type Strategy'),
            'status': _('Status'),
            'failure_code': _('Failure Code'),
            'scheduled_date': _('Scheduled Date'),
            'message': _('Message'),
            'end_to_end_id': _('End-to-End ID'),
            'internal_note': _('Internal Note'),
            'custom_id': _('Custom ID'),
            'custom_metadata': _('Custom Metadata')
        }
    
    def clean_amount(self):
        """
        Validate the amount field.
        
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If amount is negative or zero
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_('Amount must be greater than zero'))
        return amount


class SepaTransactionForm(forms.ModelForm):
    """
    Form for creating and editing SepaTransaction instances.
    
    Provides fields for SEPA transaction details, including sender,
    recipient, and amount information.
    """
    class Meta:
        """
        Metadata for the SepaTransactionForm.
        """
        model = SepaTransaction
        fields = [
            'transaction_id', 'sender_iban', 'recipient_iban', 
            'recipient_name', 'amount', 'currency', 'status'
        ]
        widgets = {
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'sender_iban': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'recipient_iban': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        help_texts = {
            'sender_iban': _('IBAN of the sending account'),
            'recipient_iban': _('IBAN of the receiving account'),
            'recipient_name': _('Name of the recipient'),
            'amount': _('Transaction amount (positive number)'),
            'currency': _('Currency for the transaction'),
            'status': _('Current status of the transaction')
        }
        labels = {
            'transaction_id': _('Transaction ID'),
            'sender_iban': _('Sender IBAN'),
            'recipient_iban': _('Recipient IBAN'),
            'recipient_name': _('Recipient Name'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'status': _('Status')
        }
    
    def clean_amount(self):
        """
        Validate the amount field.
        
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If amount is negative or zero
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_('Amount must be greater than zero'))
        return amount


class SEPA2Form(forms.ModelForm):
    """
    Form for creating and editing SEPA2 instances.
    
    Provides fields for SEPA2 transfer details, including account and
    beneficiary information.
    """
    class Meta:
        """
        Metadata for the SEPA2Form.
        """
        model = SEPA2
        fields = [
            'account_name', 'account_iban', 'account_bic', 'account_bank', 
            'amount', 'currency', 'beneficiary_name', 'beneficiary_iban', 
            'beneficiary_bic', 'beneficiary_bank', 'status', 'purpose_code', 
            'internal_note'
        ]
        widgets = {
            'account_name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_iban': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_bic': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_bank': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary_name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary_iban': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary_bic': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiary_bank': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'purpose_code': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'internal_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        help_texts = {
            'account_name': _('Name of the source account holder'),
            'account_iban': _('IBAN of the source account'),
            'account_bic': _('BIC of the source bank'),
            'account_bank': _('Name of the source bank'),
            'amount': _('Transfer amount (positive number)'),
            'currency': _('Currency for the transfer'),
            'beneficiary_name': _('Name of the beneficiary'),
            'beneficiary_iban': _('IBAN of the beneficiary account'),
            'beneficiary_bic': _('BIC of the beneficiary bank'),
            'beneficiary_bank': _('Name of the beneficiary bank'),
            'status': _('Current status of the transfer'),
            'purpose_code': _('Purpose code for the transfer'),
            'internal_note': _('Notes for internal use only')
        }
        labels = {
            'account_name': _('Account Name'),
            'account_iban': _('Account IBAN'),
            'account_bic': _('Account BIC'),
            'account_bank': _('Account Bank'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'beneficiary_name': _('Beneficiary Name'),
            'beneficiary_iban': _('Beneficiary IBAN'),
            'beneficiary_bic': _('Beneficiary BIC'),
            'beneficiary_bank': _('Beneficiary Bank'),
            'status': _('Status'),
            'purpose_code': _('Purpose Code'),
            'internal_note': _('Internal Note')
        }
    
    def clean_amount(self):
        """
        Validate the amount field.
        
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If amount is negative or zero
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_('Amount must be greater than zero'))
        return amount


class SEPA3Form(forms.ModelForm):
    """
    Form for creating and editing SEPA3 instances.
    
    Provides fields for enhanced SEPA transfer details, including sender,
    recipient, and additional reference information.
    """
    class Meta:
        """
        Metadata for the SEPA3Form.
        """
        model = SEPA3
        fields = [
            'sender_name', 'sender_iban', 'sender_bic', 'sender_bank',
            'recipient_name', 'recipient_iban', 'recipient_bic', 'recipient_bank',
            'amount', 'currency', 'status', 'reference',
            'unstructured_remittance_info', 'created_by'
        ]
        widgets = {
            'created_by': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sender_name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sender_iban': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sender_bic': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sender_bank': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recipient_name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recipient_iban': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recipient_bic': forms.Select(attrs={
                'class': 'form-control'
            }),
            'recipient_bank': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'unstructured_remittance_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        help_texts = {
            'sender_name': _('Name of the sender'),
            'sender_iban': _('IBAN of the sending account'),
            'sender_bic': _('BIC of the sending bank'),
            'sender_bank': _('Name of the sending bank'),
            'recipient_name': _('Name of the recipient'),
            'recipient_iban': _('IBAN of the receiving account'),
            'recipient_bic': _('BIC of the receiving bank'),
            'recipient_bank': _('Name of the receiving bank'),
            'amount': _('Transfer amount (positive number)'),
            'currency': _('Currency for the transfer'),
            'status': _('Current status of the transfer'),
            'reference': _('Reference for the transfer'),
            'unstructured_remittance_info': _('Additional information for the recipient'),
            'created_by': _('User who created the transfer')
        }
        labels = {
            'sender_name': _('Sender Name'),
            'sender_iban': _('Sender IBAN'),
            'sender_bic': _('Sender BIC'),
            'sender_bank': _('Sender Bank'),
            'recipient_name': _('Recipient Name'),
            'recipient_iban': _('Recipient IBAN'),
            'recipient_bic': _('Recipient BIC'),
            'recipient_bank': _('Recipient Bank'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'status': _('Status'),
            'reference': _('Reference'),
            'unstructured_remittance_info': _('Remittance Information'),
            'created_by': _('Created By')
        }
    
    def clean_amount(self):
        """
        Validate the amount field.
        
        Returns:
            Decimal: The validated amount
            
        Raises:
            ValidationError: If amount is negative or zero
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_('Amount must be greater than zero'))
        return amount


class TransferSearchForm(forms.Form):
    """
    Form for searching transfers.
    
    Provides fields for filtering transfers by various criteria.
    """
    reference = forms.CharField(
        label=_('Reference'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[('', _('All'))] + [('PDNG', _('Pending')), ('ACCP', _('Accepted')), ('RJCT', _('Rejected'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        label=_('From Date'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('To Date'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    amount_min = forms.DecimalField(
        label=_('Minimum Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    amount_max = forms.DecimalField(
        label=_('Maximum Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        """
        Perform cross-field validation for search criteria.
        
        Returns:
            dict: The cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', _('End date must be later than start date'))
        
        # Validate amount range
        if amount_min is not None and amount_max is not None and amount_min > amount_max:
            self.add_error('amount_max', _('Maximum amount must be greater than minimum amount'))
        
        return cleaned_data
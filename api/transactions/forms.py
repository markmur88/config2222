"""
Forms for the Transactions application.

This module defines form classes for handling transaction-related data,
including standard transactions and SEPA transfers.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from api.transactions.models import Transaction, SEPA


class TransactionForm(forms.ModelForm):
    """
    Form for creating and editing Transaction instances.
    
    Provides fields for basic transaction details, including accounts,
    amounts, dates, and notes.
    """
    class Meta:
        """
        Metadata for the TransactionForm.
        """
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
            'source_account': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': _('Select source account')
            }),
            'destination_account': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': _('Select destination account')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter amount'),
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'direction': forms.Select(attrs={
                'class': 'form-control'
            }),
            'request_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'execution_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'counterparty_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter counterparty name')
            }),
            'internal_note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Add internal notes'),
                'rows': 3
            }),
        }
        help_texts = {
            'amount': _('Transaction amount (positive number)'),
            'currency': _('Currency for the transaction'),
            'direction': _('Whether the transaction is outgoing (debit) or incoming (credit)'),
            'request_date': _('When the transaction was requested'),
            'execution_date': _('When the transaction should be executed'),
            'internal_note': _('Notes for internal use only (not visible to customer)'),
        }
        labels = {
            'source_account': _('Source Account'),
            'destination_account': _('Destination Account'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'direction': _('Direction'),
            'request_date': _('Request Date'),
            'execution_date': _('Execution Date'),
            'counterparty_name': _('Counterparty Name'),
            'internal_note': _('Internal Note'),
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
    
    def clean(self):
        """
        Perform cross-field validation.
        
        Returns:
            dict: The cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        request_date = cleaned_data.get('request_date')
        execution_date = cleaned_data.get('execution_date')
        
        if request_date and execution_date and execution_date < request_date:
            self.add_error('execution_date', _('Execution date cannot be earlier than request date'))
        
        return cleaned_data


class SEPAForm(forms.ModelForm):
    """
    Form for creating and editing SEPA transfer instances.
    Provides fields for SEPA-specific transfer details, including
    beneficiary information, amount, and transfer type.
    """
    # Add a read-only display field for transaction_id
    transaction_id_display = forms.CharField(
        required=False,
        label=_('Transaction ID'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        }),
        help_text=_('Unique transaction identifier')
    )
    
    class Meta:
        """
        Metadata for the SEPAForm.
        """
        model = SEPA
        fields = [
            # Remove transaction_id from here
            'beneficiary_name',
            'amount',
            'currency',
            'transfer_type',
            'type_strategy',
            'status',
            'direction',
            'internal_note',
            'custom_metadata',
        ]
        widgets = {
            # Remove transaction_id widget
            'beneficiary_name': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': _('Select beneficiary')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter amount'),
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
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
            'direction': forms.Select(attrs={
                'class': 'form-control'
            }),
            'internal_note': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Add internal notes'),
                'rows': 3
            }),
            'custom_metadata': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Add custom metadata in JSON format'),
                'rows': 3
            }),
        }
        help_texts = {
            # Remove transaction_id help_text
            'beneficiary_name': _('Recipient of the transfer'),
            'amount': _('Transfer amount (positive number)'),
            'currency': _('Currency for the transfer'),
            'transfer_type': _('Type of SEPA transfer'),
            'type_strategy': _('Strategy for handling the transfer type'),
            'status': _('Current status of the transfer'),
            'direction': _('Whether the transfer is outgoing (debit) or incoming (credit)'),
            'internal_note': _('Notes for internal use only'),
            'custom_metadata': _('Additional JSON metadata for this transfer'),
        }
        labels = {
            # Remove transaction_id label
            'beneficiary_name': _('Beneficiary'),
            'amount': _('Amount'),
            'currency': _('Currency'),
            'transfer_type': _('Transfer Type'),
            'type_strategy': _('Type Strategy'),
            'status': _('Status'),
            'direction': _('Direction'),
            'internal_note': _('Internal Note'),
            'custom_metadata': _('Custom Metadata'),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with the transaction ID if available.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        # If editing an existing instance, display the transaction_id
        if self.instance and hasattr(self.instance, 'transaction_id') and self.instance.transaction_id:
            self.fields['transaction_id_display'].initial = self.instance.transaction_id
    
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
    
    def clean_custom_metadata(self):
        """
        Validate custom metadata is valid JSON.
        
        Returns:
            str: The validated metadata
            
        Raises:
            ValidationError: If metadata is not valid JSON
        """
        metadata = self.cleaned_data.get('custom_metadata')
        if metadata:
            try:
                import json
                json.loads(metadata)
            except json.JSONDecodeError:
                raise forms.ValidationError(_('Custom metadata must be valid JSON'))
        return metadata

class TransactionSearchForm(forms.Form):
    """
    Form for searching transactions.
    
    Provides fields for filtering transactions by various criteria.
    """
    counterparty = forms.CharField(
        label=_('Counterparty'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
    direction = forms.ChoiceField(
        label=_('Direction'),
        required=False,
        choices=[('', _('All')), ('debit', _('Debit')), ('credit', _('Credit'))],
        widget=forms.Select(attrs={'class': 'form-control'})
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
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Validate amount range
        if amount_min is not None and amount_max is not None and amount_min > amount_max:
            self.add_error('amount_max', _('Maximum amount must be greater than minimum amount'))
        
        # Validate date range
        if date_from is not None and date_to is not None and date_from > date_to:
            self.add_error('date_to', _('End date must be later than start date'))
        
        return cleaned_data
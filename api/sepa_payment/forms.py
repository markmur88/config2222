"""
Forms for the SEPA Payment application.

This module defines form classes for handling SEPA payment data input,
including validation and formatting of SEPA credit transfers.
"""
import random
import string
import uuid
from datetime import date
from typing import Any, Dict

from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from api.sepa_payment.models import SepaCreditTransfer


class SepaCreditTransferForm(forms.ModelForm):
    """
    Form for creating and editing SEPA Credit Transfers.
    
    Provides a user interface for creating SEPA credit transfers with
    validation and automatic generation of required identifiers.
    """
    class Meta:
        """
        Metadata for the SepaCreditTransferForm.
        
        Defines the model, fields, widgets, and other form configuration.
        """
        model = SepaCreditTransfer
        fields = [
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
            'remittance_unstructured'
        ]
        widgets = {
            'purpose_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., SALA')
            }),
            'requested_execution_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat()
            }),
            'debtor_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('e.g., John Doe')
            }),
            'debtor_iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., DE89370400440532013000')
            }),
            'debtor_currency': forms.Select(attrs={'class': 'form-control'}),
            'debtor_address_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., DE')
            }),
            'debtor_address_street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Main Street 123')
            }),
            'debtor_address_zip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 10115 Berlin')
            }),
            'creditor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Company Ltd')
            }),
            'creditor_iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., FR7630006000011234567890189')
            }),
            'creditor_currency': forms.Select(attrs={'class': 'form-control'}),
            'creditor_address_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., FR')
            }),
            'creditor_address_street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Rue de Paris 456')
            }),
            'creditor_address_zip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 75001 Paris')
            }),
            'creditor_agent_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., BANKFRPPXXX')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': _('e.g., 1000.00')
            }),
            'end_to_end_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'instruction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'remittance_structured': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., RF18539007547034')
            }),
            'remittance_unstructured': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Invoice 12345')
            }),
        }
        help_texts = {
            'purpose_code': _('Code identifying the purpose of the SEPA transfer'),
            'requested_execution_date': _('Date when the payment should be executed'),
            'debtor_name': _('Name of the account owner (sender)'),
            'debtor_iban': _('IBAN of the sender account'),
            'debtor_currency': _('Currency of the sender account'),
            'creditor_name': _('Name of the beneficiary (recipient)'),
            'creditor_iban': _('IBAN of the recipient account'),
            'creditor_currency': _('Currency of the recipient account'),
            'amount': _('Amount to transfer'),
            'end_to_end_id': _('Unique identifier for end-to-end tracking'),
            'instruction_id': _('Unique identifier for this instruction'),
            'remittance_structured': _('Structured remittance information'),
            'remittance_unstructured': _('Unstructured remittance information'),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with customizations.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        
        # Apply form-control class to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-control'})
        
        # Generate UUIDs if they don't exist
        if not self.instance.end_to_end_id:
            self.instance.end_to_end_id = self._generate_uuid()
        if not self.instance.instruction_id:
            self.instance.instruction_id = self._generate_uuid()
        
        # Show generated values in the form
        self.fields['end_to_end_id'].initial = self.instance.end_to_end_id
        self.fields['instruction_id'].initial = self.instance.instruction_id
    
    def _generate_random_id(self) -> str:
        """
        Generate a random ID that meets SEPA requirements.
        
        Returns:
            str: A random ID with exactly 35 characters
        """
        # Generate a random ID with exactly 35 characters that meets the format [a-zA-Z0-9.-]{1,35}
        return ''.join(random.choices(string.ascii_letters + string.digits + '.-', k=35))
    
    def _generate_uuid(self) -> str:
        """
        Generate a UUID in string format.
        
        Returns:
            str: A new UUID as string
        """
        return str(uuid.uuid4())
    
    def clean_debtor_iban(self) -> str:
        """
        Validate the debtor IBAN format.
        
        Returns:
            str: The validated IBAN
            
        Raises:
            forms.ValidationError: If IBAN format is invalid
        """
        iban = self.cleaned_data.get('debtor_iban')
        if iban:
            # Remove spaces
            iban = iban.replace(' ', '')
            
            # Basic validation - improve with a proper IBAN validation library
            if len(iban) < 15 or len(iban) > 34:
                raise forms.ValidationError(_("Invalid IBAN length"))
            
            # Convert to uppercase
            iban = iban.upper()
        
        return iban
    
    def clean_creditor_iban(self) -> str:
        """
        Validate the creditor IBAN format.
        
        Returns:
            str: The validated IBAN
            
        Raises:
            forms.ValidationError: If IBAN format is invalid
        """
        iban = self.cleaned_data.get('creditor_iban')
        if iban:
            # Remove spaces
            iban = iban.replace(' ', '')
            
            # Basic validation - improve with a proper IBAN validation library
            if len(iban) < 15 or len(iban) > 34:
                raise forms.ValidationError(_("Invalid IBAN length"))
            
            # Convert to uppercase
            iban = iban.upper()
        
        return iban
    
    def clean_amount(self) -> float:
        """
        Validate that the amount is positive.
        
        Returns:
            float: The validated amount
            
        Raises:
            forms.ValidationError: If amount is not positive
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_("Amount must be greater than zero"))
        return amount
    
    def clean_requested_execution_date(self) -> date:
        """
        Validate that the execution date is not in the past.
        
        Returns:
            date: The validated execution date
            
        Raises:
            forms.ValidationError: If date is in the past
        """
        execution_date = self.cleaned_data.get('requested_execution_date')
        if execution_date and execution_date < date.today():
            raise forms.ValidationError(_("Execution date cannot be in the past"))
        return execution_date


class SepaCreditTransferSearchForm(forms.Form):
    """
    Form for searching SEPA credit transfers.
    
    Provides fields for filtering SEPA transfers in list views.
    """
    debtor_name = forms.CharField(
        label=_('Debtor Name'),
        required=False,
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    creditor_name = forms.CharField(
        label=_('Creditor Name'),
        required=False,
        max_length=70,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    min_amount = forms.DecimalField(
        label=_('Min Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    max_amount = forms.DecimalField(
        label=_('Max Amount'),
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    date_from = forms.DateField(
        label=_('Date From'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label=_('Date To'),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[('', _('All'))] + [('PDNG', _('Pending')), ('ACCP', _('Accepted')), ('RJCT', _('Rejected'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
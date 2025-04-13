"""
Forms for the Sandbox application.

This module defines form classes for handling sandbox-related data input,
such as simulated incoming collections and test transactions.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from api.sandbox.models import IncomingCollection
from api.core.choices import CURRENCY_CODES


class IncomingCollectionForm(forms.ModelForm):
    """
    Form for creating and editing simulated incoming collections.
    
    Provides a user interface for testing collection processing
    without requiring actual bank transactions.
    """
    class Meta:
        """
        Metadata for the IncomingCollectionForm.
        
        Defines the model, fields, widgets, and other form configuration.
        """
        model = IncomingCollection
        fields = [
            'reference_id', 
            'amount', 
            'currency', 
            'sender_name', 
            'sender_iban', 
            'recipient_iban',
            'status'
        ]
        widgets = {
            'reference_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., REF123456789')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': _('e.g., 1000.00')
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sender_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., John Doe')
            }),
            'sender_iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., DE89370400440532013000')
            }),
            'recipient_iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., FR7630006000011234567890189')
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        help_texts = {
            'reference_id': _('Unique identifier for this collection'),
            'amount': _('Amount to be collected'),
            'currency': _('Currency of the amount'),
            'sender_name': _('Name of the sending party'),
            'sender_iban': _('IBAN of the sending account'),
            'recipient_iban': _('IBAN of the receiving account'),
            'status': _('Current status of the collection'),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with customizations.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        
        # Make currency a select field with predefined choices
        self.fields['currency'].widget = forms.Select(
            choices=CURRENCY_CODES,
            attrs={'class': 'form-control'}
        )
    
    def clean_sender_iban(self):
        """
        Validate the sender IBAN format.
        
        Returns:
            str: The validated sender IBAN
            
        Raises:
            forms.ValidationError: If IBAN format is invalid
        """
        iban = self.cleaned_data.get('sender_iban')
        if iban:
            # Remove spaces
            iban = iban.replace(' ', '')
            
            # Basic validation - improve with a proper IBAN validation library
            if len(iban) < 15 or len(iban) > 34:
                raise forms.ValidationError(_('Invalid IBAN length'))
            
            # Convert to uppercase
            iban = iban.upper()
        
        return iban
    
    def clean_recipient_iban(self):
        """
        Validate the recipient IBAN format.
        
        Returns:
            str: The validated recipient IBAN
            
        Raises:
            forms.ValidationError: If IBAN format is invalid
        """
        iban = self.cleaned_data.get('recipient_iban')
        if iban:
            # Remove spaces
            iban = iban.replace(' ', '')
            
            # Basic validation - improve with a proper IBAN validation library
            if len(iban) < 15 or len(iban) > 34:
                raise forms.ValidationError(_('Invalid IBAN length'))
            
            # Convert to uppercase
            iban = iban.upper()
        
        return iban
    
    def clean_amount(self):
        """
        Validate the amount is positive.
        
        Returns:
            float: The validated amount
            
        Raises:
            forms.ValidationError: If amount is not positive
        """
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(_('Amount must be greater than zero'))
        return amount


class IncomingCollectionSearchForm(forms.Form):
    """
    Form for searching incoming collections.
    
    Provides fields for filtering the list of incoming collections.
    """
    reference_id = forms.CharField(
        label=_('Reference ID'),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    sender_name = forms.CharField(
        label=_('Sender Name'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[('', _('All'))] + [('PENDING', _('Pending')), ('COMPLETED', _('Completed'))],
        widget=forms.Select(attrs={'class': 'form-control'})
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


class SandboxSettingsForm(forms.Form):
    """
    Form for configuring sandbox settings.
    
    Allows administrators to configure how the sandbox environment behaves.
    """
    auto_approve_collections = forms.BooleanField(
        label=_('Auto-approve incoming collections'),
        required=False,
        help_text=_('Automatically approve incoming collections without manual review'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    simulated_delay = forms.IntegerField(
        label=_('Simulated processing delay (seconds)'),
        required=False,
        min_value=0,
        max_value=60,
        help_text=_('Simulate processing delay to mimic real-world conditions'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '60'})
    )
    error_rate = forms.IntegerField(
        label=_('Simulated error rate (%)'),
        required=False,
        min_value=0,
        max_value=100,
        help_text=_('Percentage of transactions that will randomly fail'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'})
    )
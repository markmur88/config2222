"""
Forms for the Collection application.

This module defines form classes for handling collection-related data input,
including mandate creation and collection requests.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from api.collection.models import Mandate, Collection


class MandateForm(forms.ModelForm):
    """
    Form for creating and editing mandates.
    
    A mandate represents authorization from a debtor to collect funds from their account.
    """
    class Meta:
        """
        Metadata for the MandateForm.
        
        Defines the model, fields, widgets, and other form configuration.
        """
        model = Mandate
        fields = [
            'scheme', 
            'debtor_name', 
            'debtor_iban', 
            'signature_date', 
            'contract_reference', 
            'is_active'
        ]
        widgets = {
            'signature_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'scheme': forms.Select(attrs={'class': 'form-control'}),
            'debtor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_iban': forms.TextInput(attrs={'class': 'form-control'}),
            'contract_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'scheme': _('The direct debit scheme (e.g., SEPA Core, SEPA B2B)'),
            'debtor_name': _('Full name of the account holder'),
            'debtor_iban': _('IBAN of the debtor account'),
            'signature_date': _('Date when the mandate was signed'),
            'contract_reference': _('Reference number for the mandate agreement'),
            'is_active': _('Whether this mandate is currently active'),
        }
    
    def clean_debtor_iban(self):
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
                raise forms.ValidationError(_('Invalid IBAN length'))
            
            # Convert to uppercase
            iban = iban.upper()
        
        return iban


class CollectionForm(forms.ModelForm):
    """
    Form for creating and editing collections.
    
    A collection represents a request to collect money from a debtor account
    based on a previously established mandate.
    """
    class Meta:
        """
        Metadata for the CollectionForm.
        
        Defines the model, fields, widgets, and other form configuration.
        """
        model = Collection
        fields = [
            'mandate', 
            'scheduled_date', 
            'amount',
            'local_iban', 
            'message', 
            'internal_note', 
            'custom_metadata'
        ]
        widgets = {
            'mandate': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'local_iban': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.TextInput(attrs={'class': 'form-control'}),
            'internal_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'custom_metadata': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'mandate': _('The mandate authorizing this collection'),
            'scheduled_date': _('Date when the collection should be executed'),
            'amount': _('Amount to collect'),
            'local_iban': _('IBAN of the account receiving the funds'),
            'message': _('Message to be shown to the debtor'),
            'internal_note': _('Notes for internal use only'),
            'custom_metadata': _('Additional metadata for integration purposes'),
        }
    
    def clean(self):
        """
        Perform cross-field validation for the collection form.
        
        Returns:
            dict: The cleaned data
            
        Raises:
            forms.ValidationError: If validation fails
        """
        cleaned_data = super().clean()
        mandate = cleaned_data.get('mandate')
        
        # Ensure the mandate is active
        if mandate and not mandate.is_active:
            self.add_error('mandate', _('Cannot create a collection with an inactive mandate'))
        
        # Add more validation as needed
        return cleaned_data


class MandateSearchForm(forms.Form):
    """
    Form for searching mandates.
    """
    debtor_name = forms.CharField(
        label=_('Debtor Name'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    debtor_iban = forms.CharField(
        label=_('Debtor IBAN'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[('', _('All')), ('True', _('Active')), ('False', _('Inactive'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CollectionSearchForm(forms.Form):
    """
    Form for searching collections.
    """
    debtor_name = forms.CharField(
        label=_('Debtor Name'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        label=_('Date From'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        label=_('Date To'),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[
            ('', _('All')), 
            ('pending', _('Pending')), 
            ('processed', _('Processed')),
            ('failed', _('Failed'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
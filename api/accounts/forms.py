"""
Forms for the Accounts application.

This module defines form classes used for handling account-related data,
including creation and editing of account records.
"""
from django import forms
from api.accounts.models import Account


class AccountForm(forms.ModelForm):
    """
    Form for creating and editing Account instances.
    
    Provides a user-friendly interface with styled form fields
    for all Account model attributes.
    """
    class Meta:
        """
        Metadata for the AccountForm.
        
        Defines the model, fields, and styling for the form.
        """
        model = Account
        fields = [
            'name', 
            'status', 
            'balance', 
            'currency', 
            'iban', 
            'type', 
            'is_main'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'is_main': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def clean_balance(self):
        """
        Validate the balance field.
        
        Ensures the balance is a positive number.
        
        Returns:
            Decimal: The validated balance
            
        Raises:
            ValidationError: If balance is negative
        """
        balance = self.cleaned_data.get('balance')
        if balance is not None and balance < 0:
            raise forms.ValidationError("Balance cannot be negative.")
        return balance
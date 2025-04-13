"""
Forms for the Core application.
This module defines form classes for handling core application data,
including IBAN and debtor information.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from api.core.models import CoreModel, IBAN, Debtor

# Either remove this class completely:
# class CoreModelForm(forms.ModelForm):
#     """
#     Base form for CoreModel instances.
#     Provides common fields and widgets that can be inherited
#     by other forms based on CoreModel.
#     """
#     class Meta:
#         """
#         Metadata for the CoreModelForm.
#         """
#         model = CoreModel
#         fields = ['name', 'description']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Enter name')}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter description')}),
#         }
#         help_texts = {
#             'name': _('A short, descriptive name'),
#             'description': _('Detailed description of this item'),
#         }

# Or modify it to use only fields that actually exist in CoreModel:
class CoreModelForm(forms.ModelForm):
    """
    Base form for CoreModel instances.
    Provides common fields and widgets that can be inherited
    by other forms based on CoreModel.
    """
    class Meta:
        """
        Metadata for the CoreModelForm.
        """
        model = CoreModel
        fields = []  # CoreModel is abstract and has no fields meant for end-user editing
        
        # These can be used by child classes
        widgets = {
            # Define common widgets here if needed
        }
        help_texts = {
            # Define common help texts here if needed
        }

class IBANForm(forms.ModelForm):
    """
    Form for creating and editing IBAN instances.
    Provides fields for IBAN details including bank information
    and account settings.
    """
    class Meta:
        """
        Metadata for the IBANForm.
        """
        model = IBAN
        fields = ['iban', 'bic', 'bank_name', 'status', 'type', 'allow_collections']
        widgets = {
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., DE89370400440532013000')
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., DEUTDEFFXXX')
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Deutsche Bank')
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'allow_collections': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'iban': _('International Bank Account Number - no spaces'),
            'bic': _('Bank Identifier Code (8 or 11 characters)'),
            'bank_name': _('Name of the financial institution'),
            'status': _('Current status of this IBAN'),
            'type': _('Account type'),
            'allow_collections': _('Whether direct debits are allowed from this account'),
        }

    def clean_iban(self):
        """
        Validate the IBAN format.
        
        Returns:
            str: The validated IBAN
            
        Raises:
            ValidationError: If IBAN format is invalid
        """
        iban = self.cleaned_data.get('iban')
        if iban:
            # Remove spaces
            iban = iban.replace(' ', '')
            # Basic validation - improve with a proper IBAN validation library
            if len(iban) < 15 or len(iban) > 34:
                raise forms.ValidationError(_('Invalid IBAN length'))
            # Convert to uppercase
            iban = iban.upper()
        return iban

    def clean_bic(self):
        """
        Validate the BIC format.
        
        Returns:
            str: The validated BIC
            
        Raises:
            ValidationError: If BIC format is invalid
        """
        bic = self.cleaned_data.get('bic')
        if bic:
            # Remove spaces
            bic = bic.replace(' ', '')
            # Basic validation
            if len(bic) not in [8, 11]:
                raise forms.ValidationError(_('BIC must be 8 or 11 characters'))
            # Convert to uppercase
            bic = bic.upper()
        return bic

class DebtorForm(forms.ModelForm):
    """
    Form for creating and editing Debtor instances.
    Provides fields for debtor details including contact information.
    """
    class Meta:
        """
        Metadata for the DebtorForm.
        """
        model = Debtor
        fields = ['iban', 'name', 'street', 'building_number', 'postal_code', 'city', 'country']
        widgets = {
            'iban': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Full name of individual or organization')
            }),
            'street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Street name')
            }),
            'building_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Building number')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal code')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City')
            }),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'iban': _('Select the debtor\'s IBAN'),
            'name': _('Full legal name of the debtor'),
            'street': _('Street name without the building number'),
            'building_number': _('Building or house number'),
            'postal_code': _('Postal or ZIP code'),
            'city': _('City or town name'),
            'country': _('Country code (2 letters)'),
        }

    def clean_postal_code(self):
        """
        Validate postal code format.
        
        Returns:
            str: The validated postal code
            
        Raises:
            ValidationError: If postal code format is invalid
        """
        postal_code = self.cleaned_data.get('postal_code')
        country = self.cleaned_data.get('country')
        
        if postal_code and country:
            # Example validation for specific countries
            if country == 'DE' and not postal_code.isdigit():
                raise forms.ValidationError(_('German postal codes should only contain digits'))
            if country == 'GB' and not postal_code.strip():
                raise forms.ValidationError(_('UK postal codes are required'))
                
        return postal_code

class IBANSearchForm(forms.Form):
    """
    Form for searching IBAN records.
    """
    iban = forms.CharField(
        label=_('IBAN'),
        required=False,
        max_length=34,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    bank_name = forms.CharField(
        label=_('Bank Name'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label=_('Status'),
        required=False,
        choices=[('', _('All'))] + [('active', _('Active')), ('inactive', _('Inactive'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    type = forms.ChoiceField(
        label=_('Type'),
        required=False,
        choices=[('', _('All'))] + [('main', _('Main')), ('virtual', _('Virtual'))],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class DebtorSearchForm(forms.Form):
    """
    Form for searching Debtor records.
    """
    name = forms.CharField(
        label=_('Name'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    iban = forms.CharField(
        label=_('IBAN'),
        required=False,
        max_length=34,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        label=_('City'),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    country = forms.CharField(
        label=_('Country'),
        required=False,
        max_length=2,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
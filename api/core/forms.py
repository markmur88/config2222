from django import forms
from api.core.models import CoreModel, IBAN, Debtor

# class CoreModelForm(forms.ModelForm):
#     class Meta:
#         model = CoreModel
#         fields = ['name', 'description']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control'}),
#         }

class IBANForm(forms.ModelForm):
    class Meta:
        model = IBAN
        fields = ['iban', 'bic', 'bank_name', 'status', 'type', 'allow_collections']
        widgets = {
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'bic': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'allow_collections': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = ['iban', 'name', 'street', 'building_number', 'postal_code', 'city', 'country']
        widgets = {
            'iban': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'building_number': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

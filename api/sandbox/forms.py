from django import forms
from api.sandbox.models import IncomingCollection

class IncomingCollectionForm(forms.ModelForm):
    class Meta:
        model = IncomingCollection
        fields = ['reference_id', 'amount', 'currency', 'sender_name', 'sender_iban', 'recipient_iban']
        widgets = {
            'reference_id': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_iban': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_iban': forms.TextInput(attrs={'class': 'form-control'}),
        }

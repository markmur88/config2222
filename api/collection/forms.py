from django import forms
from api.collection.models import Mandate, Collection

class MandateForm(forms.ModelForm):
    class Meta:
        model = Mandate
        fields = ['scheme', 'debtor_name', 'debtor_iban', 'signature_date', 'contract_reference', 'is_active']
        widgets = {
            'signature_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['mandate', 'scheduled_date', 'local_iban', 'message', 'internal_note', 'custom_metadata']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
        }

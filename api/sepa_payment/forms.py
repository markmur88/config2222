# apps/sepa_payment/forms.py
from django import forms
from api.sepa_payment.models import SepaCreditTransfer
from django.core.validators import RegexValidator
import random
import string
import uuid  # Importar módulo para generar UUIDs

class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
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
            'requested_execution_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        # Generar automáticamente un UUID si no está definido
        if not self.instance.end_to_end_id:
            self.instance.end_to_end_id = self._generate_uuid()
        if not self.instance.instruction_id:
            self.instance.instruction_id = self._generate_uuid()
        # Mostrar los valores generados en el formulario
        self.fields['end_to_end_id'].initial = self.instance.end_to_end_id
        self.fields['instruction_id'].initial = self.instance.instruction_id

    def _generate_random_id(self):
        # Genera un ID aleatorio con exactamente 35 caracteres que cumple con el formato [a-zA-Z0-9.-]{1,35}
        return ''.join(random.choices(string.ascii_letters + string.digits + '.-', k=35))

    def _generate_uuid(self):
        # Genera un UUID en formato de cadena
        return str(uuid.uuid4())
# apps/sepa_payment/services.py
import os
import requests
import json
from config import settings
from django.core.exceptions import ImproperlyConfigured
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
from api.sepa_payment.models import SepaCreditTransfer, SepaCreditTransferError, SepaCreditTransferStatus

class SepaPaymentService:
    def __init__(self):
        self.api_base_url = settings.API_BASE_URL
        self.client_id = settings.API_CLIENT_ID
        self.client_secret = settings.API_CLIENT_SECRET
        self.access_token = None
        
        if not all([self.api_base_url, self.client_id, self.client_secret]):
            raise ImproperlyConfigured('Faltan configurar las variables de entorno para la API')

    def _get_access_token(self):
        if not self.access_token:
            auth_url = f"{self.api_base_url}/oauth2/token"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(auth_url, headers=headers, data=data)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
            else:
                raise Exception(f'Error al obtener token: {response.text}')
        
        return self.access_token

    def create_payment(self, data):
        # access_token = self._get_access_token()
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Request-ID': self._generate_request_id(),
            # 'PSU-ID': 'YOUR_USER_ID',
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'
        }
        
        payload = {
            'purposeCode': data['purpose_code'],
            'requestedExecutionDate': data['requested_execution_date'].strftime('%Y-%m-%d'),
            'debtor': {
                'name': data['debtor_name'],
                'postalAddress': {
                    'country': data['debtor_address_country'],
                    'addressLine': [
                        f"{data['debtor_address_street']}, {data['debtor_address_zip']}"
                    ]
                }
            },
            'debtorAccount': {
                'iban': data['debtor_iban'],
                'currency': data['debtor_currency']
            },
            'paymentIdentification': {
                'endToEndId': data['end_to_end_id'],
                'instructionId': data['instruction_id']
            },
            'instructedAmount': {
                'amount': str(data['amount']),
                'currency': data['creditor_currency']
            },
            'creditorAgent': {
                'financialInstitutionId': data['creditor_agent_id']
            },
            'creditor': {
                'name': data['creditor_name'],
                'postalAddress': {
                    'country': data['creditor_address_country'],
                    'addressLine': [
                        f"{data['creditor_address_street']}, {data['creditor_address_zip']}"
                    ]
                }
            },
            'creditorAccount': {
                'iban': data['creditor_iban'],
                'currency': data['creditor_currency']
            },
            'remittanceInformationStructured': data['remittance_structured'],
            'remittanceInformationUnstructured': data['remittance_unstructured']
        }
        
        response = requests.post(self.api_base_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            return response.json()['paymentId']
        else:
            raise Exception(f'Error al crear el pago: {response.text}')

    def get_payment_status(self, payment_id):
        # access_token = self._get_access_token()
        access_token = os.getenv("ACCESS_TOKEN")
        psu_id = os.getenv("PSU_ID")
        psu_ip_address = os.getenv("PSU_IP_ADDRESS")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Request-ID': self._generate_request_id()
        }
        
        response = requests.get(f"{self.api_base_url}/{payment_id}/status", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Error al obtener el estado del pago: {response.text}')

    def _generate_request_id(self):
        return f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    
    def update_payment_status(self, payment_id, status):
        """
        Actualiza el estado de una transferencia y registra el cambio.
        """
        try:
            payment = SepaCreditTransfer.objects.get(payment_id=payment_id)
            SepaCreditTransferStatus.objects.create(
                payment=payment,
                status=status,
                timestamp=timezone.now()
            )
            return True
        except SepaCreditTransfer.DoesNotExist:
            raise Exception(f'No se encontró la transferencia con ID: {payment_id}')
        except Exception as e:
            self._log_error(payment_id, str(e))
            raise

    def _log_error(self, payment_id, error_message):
        """
        Registra un error en la base de datos.
        """
        try:
            payment = SepaCreditTransfer.objects.get(payment_id=payment_id)
            SepaCreditTransferError.objects.create(
                payment=payment,
                error_code=999,  # Código genérico para errores internos
                error_message=error_message,
                message_id=self._generate_message_id(),
                timestamp=timezone.now()
            )
        except SepaCreditTransfer.DoesNotExist:
            # Si no existe el pago, registramos el error con payment_id como referencia
            SepaCreditTransferError.objects.create(
                payment_id=payment_id,
                error_code=999,
                error_message=error_message,
                message_id=self._generate_message_id(),
                timestamp=timezone.now()
            )

    def _generate_message_id(self):
        """
        Genera un ID único para el mensaje de error.
        """
        return f"ERR-{timezone.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
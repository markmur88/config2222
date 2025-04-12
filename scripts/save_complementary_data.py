from django.core.management.base import BaseCommand
from core.payments.models import ErrorResponse, Message, TransactionStatus, StatusResponse
from core.complementary.forms import ErrorResponseForm, MessageForm, TransactionStatusForm, StatusResponseForm

class Command(BaseCommand):
    help = 'Guardar información de los formularios complementarios en la base de datos'

    def handle(self, *args, **kwargs):
        # Datos de ejemplo para ErrorResponse
        error_response_data = {'code': 1, 'message': 'Error message example'}
        error_response_form = ErrorResponseForm(data=error_response_data)
        if error_response_form.is_valid():
            error_response_form.save()
            self.stdout.write(self.style.SUCCESS('ErrorResponse guardado exitosamente'))
        else:
            self.stdout.write(self.style.ERROR('Error al guardar ErrorResponse'))

        # Datos de ejemplo para Message
        message_data = {'code': 1, 'message': 'Message example'}
        message_form = MessageForm(data=message_data)
        if message_form.is_valid():
            message_form.save()
            self.stdout.write(self.style.SUCCESS('Message guardado exitosamente'))
        else:
            self.stdout.write(self.style.ERROR('Error al guardar Message'))

        # Datos de ejemplo para TransactionStatus
        transaction_status_data = {'transaction_status': 'ACCP'}
        transaction_status_form = TransactionStatusForm(data=transaction_status_data)
        if transaction_status_form.is_valid():
            transaction_status_form.save()
            self.stdout.write(self.style.SUCCESS('TransactionStatus guardado exitosamente'))
        else:
            self.stdout.write(self.style.ERROR('Error al guardar TransactionStatus'))

        # Datos de ejemplo para StatusResponse
        status_response_data = {'category': 'Category example', 'code': 'Code example', 'text': 'Text example'}
        status_response_form = StatusResponseForm(data=status_response_data)
        if status_response_form.is_valid():
            status_response_form.save()
            self.stdout.write(self.style.SUCCESS('StatusResponse guardado exitosamente'))
        else:
            self.stdout.write(self.style.ERROR('Error al guardar StatusResponse'))

        # Datos adicionales de ejemplo para ErrorResponse
        additional_error_responses = [
            {'code': 114, 'message': 'Unable to identify transaction by Id.'},
            {'code': 115, 'message': 'Time limit exceeded.'},
            {'code': 121, 'message': 'OTP invalid challenge response: %s.'},
            {'code': 122, 'message': 'Invalid OTP.'},
            {'code': 127, 'message': 'Booking date from must precede booking date to.'},
            {'code': 131, 'message': 'Invalid value for "sortBy". Valid values are "bookingDate[ASC]" and "bookingDate[DESC]".'},
            {'code': 132, 'message': 'not supported'},
            {'code': 138, 'message': 'it seems that you started a non pushTAN challenge. Please use the PATCH endpoint to continue'},
            {'code': 139, 'message': 'it seems that you started a pushTAN challenge. Please use the GET endpoint to continue'}
        ]
        for error_data in additional_error_responses:
            error_response_form = ErrorResponseForm(data=error_data)
            if error_response_form.is_valid():
                error_response_form.save()
                self.stdout.write(self.style.SUCCESS(f'ErrorResponse {error_data["code"]} guardado exitosamente'))
            else:
                self.stdout.write(self.style.ERROR(f'Error al guardar ErrorResponse {error_data["code"]}'))

        # Datos adicionales de ejemplo para StatusResponse
        additional_status_responses = [
            {'transaction_status': 'ACCP', 'message': {'code': '200', 'text': 'successful operation', 'category': 'Success'}},
            {'transaction_status': 'RJCT', 'message': {'code': '400', 'text': 'Invalid value for %s.', 'category': 'Error'}},
            {'transaction_status': 'RJCT', 'message': {'code': '401', 'text': 'The requested function requires a SCA Level Authentication.', 'category': 'Error'}}
        ]
        for status_data in additional_status_responses:
            status_response_form = StatusResponseForm(data=status_data)
            if status_response_form.is_valid():
                status_response_form.save()
                self.stdout.write(self.style.SUCCESS(f'StatusResponse {status_data["transaction_status"]} guardado exitosamente'))
            else:
                self.stdout.write(self.style.ERROR(f'Error al guardar StatusResponse {status_data["transaction_status"]}'))

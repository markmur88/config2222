import psycopg2
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Guardar información de los formularios complementarios en una base de datos PostgreSQL'

    def handle(self, *args, **kwargs):
        conn = psycopg2.connect(
            dbname='your_db_name',
            user='your_db_user',
            password='your_db_password',
            host='your_db_host',
            port='your_db_port'
        )
        cursor = conn.cursor()

        # Crear tablas si no existen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ErrorResponse (
                id SERIAL PRIMARY KEY,
                code INTEGER,
                message TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Message (
                id SERIAL PRIMARY KEY,
                code INTEGER,
                message TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TransactionStatus (
                id SERIAL PRIMARY KEY,
                transaction_status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS StatusResponse (
                id SERIAL PRIMARY KEY,
                category TEXT,
                code TEXT,
                text TEXT
            )
        ''')

        # Datos de ejemplo para ErrorResponse
        error_response_data = {'code': 1, 'message': 'Error message example'}
        cursor.execute('''
            INSERT INTO ErrorResponse (code, message) VALUES (%s, %s)
        ''', (error_response_data['code'], error_response_data['message']))
        self.stdout.write(self.style.SUCCESS('ErrorResponse guardado exitosamente'))

        # Datos de ejemplo para Message
        message_data = {'code': 1, 'message': 'Message example'}
        cursor.execute('''
            INSERT INTO Message (code, message) VALUES (%s, %s)
        ''', (message_data['code'], message_data['message']))
        self.stdout.write(self.style.SUCCESS('Message guardado exitosamente'))

        # Datos de ejemplo para TransactionStatus
        transaction_status_data = {'transaction_status': 'ACCP'}
        cursor.execute('''
            INSERT INTO TransactionStatus (transaction_status) VALUES (%s)
        ''', (transaction_status_data['transaction_status'],))
        self.stdout.write(self.style.SUCCESS('TransactionStatus guardado exitosamente'))

        # Datos de ejemplo para StatusResponse
        status_response_data = {'category': 'Category example', 'code': 'Code example', 'text': 'Text example'}
        cursor.execute('''
            INSERT INTO StatusResponse (category, code, text) VALUES (%s, %s, %s)
        ''', (status_response_data['category'], status_response_data['code'], status_response_data['text']))
        self.stdout.write(self.style.SUCCESS('StatusResponse guardado exitosamente'))

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
            cursor.execute('''
                INSERT INTO ErrorResponse (code, message) VALUES (%s, %s)
            ''', (error_data['code'], error_data['message']))
            self.stdout.write(self.style.SUCCESS(f'ErrorResponse {error_data["code"]} guardado exitosamente'))

        # Datos adicionales de ejemplo para StatusResponse
        additional_status_responses = [
            {'transaction_status': 'ACCP', 'message': {'code': '200', 'text': 'successful operation', 'category': 'Success'}},
            {'transaction_status': 'RJCT', 'message': {'code': '400', 'text': 'Invalid value for %s.', 'category': 'Error'}},
            {'transaction_status': 'RJCT', 'message': {'code': '401', 'text': 'The requested function requires a SCA Level Authentication.', 'category': 'Error'}}
        ]
        for status_data in additional_status_responses:
            cursor.execute('''
                INSERT INTO StatusResponse (category, code, text) VALUES (%s, %s, %s)
            ''', (status_data['message']['category'], status_data['message']['code'], status_data['message']['text']))
            self.stdout.write(self.style.SUCCESS(f'StatusResponse {status_data["transaction_status"]} guardado exitosamente'))

        conn.commit()
        conn.close()

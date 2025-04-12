import sqlite3
import os
from django.core.management.base import BaseCommand
from config import settings

class Command(BaseCommand):
    help = 'Guardar información de los formularios complementarios en una base de datos SQLite'

    def handle(self, *args, **kwargs):
        db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear tablas si no existen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_errorresponse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER,
                message TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER,
                message TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_transactionstatus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_statusresponse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                code TEXT,
                text TEXT
            )
        ''')

        # Datos de ejemplo para ErrorResponse
        payments_errorresponse = [
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
        for error_data in payments_errorresponse:
            cursor.execute('''
                INSERT INTO payments_errorresponse (code, message) VALUES (?, ?)
            ''', (error_data['code'], error_data['message']))
            self.stdout.write(self.style.SUCCESS(f'payments_errorresponse {error_data["code"]} guardado exitosamente'))

        # Datos de ejemplo para Message
        payments_message = {'code': 1, 'message': 'Message example'}
        cursor.execute('''
            INSERT INTO payments_message (code, message) VALUES (?, ?)
        ''', (payments_message['code'], payments_message['message']))
        self.stdout.write(self.style.SUCCESS('payments_message guardado exitosamente'))

        # Datos de ejemplo para TransactionStatus
        transaction_status = {'transaction_status': 'ACCP'}
        cursor.execute('''
            INSERT INTO payments_transactionstatus (transaction_status) VALUES (?)
        ''', (transaction_status['transaction_status'],))
        self.stdout.write(self.style.SUCCESS('payments_transactionstatus guardado exitosamente'))

        # Datos de ejemplo para StatusResponse
        payments_statusresponse = [
            {'category': 'Success', 'code': '200', 'text': 'successful operation'},
            {'category': 'Error', 'code': '400', 'text': 'Invalid value for %s.'},
            {'category': 'Error', 'code': '401', 'text': 'The requested function requires a SCA Level Authentication.'}
        ]
        for status_data in payments_statusresponse:
            cursor.execute('''
                INSERT INTO payments_statusresponse (category, code, text) VALUES (?, ?, ?)
            ''', (status_data['category'], status_data['code'], status_data['text']))
            self.stdout.write(self.style.SUCCESS(f'payments_statusresponse {status_data["code"]} guardado exitosamente'))

        conn.commit()
        conn.close()

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, AllowAny
from rest_framework.exceptions import APIException
from rest_framework.renderers import JSONRenderer

from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from api.transfers.models import SEPA2, Transfer, SEPA3
from api.transfers.serializers import SEPA3Serializer, SEPA3Serializer
from api.transfers.forms import SEPA2Form

from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer, sepa_transfer
from api.core.services import generate_sepa_xml

import logging
import os

logger = logging.getLogger("bank_services")

# Funciones auxiliares
def error_response(message, status_code):
    response = Response({"error": message}, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response

def success_response(data, status_code):
    response = Response(data, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response

def get_existing_record(model, key_value, key_field):
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()

def generate_success_template(transfer, sepa_xml):
    return {
        "transfer": {
            "id": transfer.id,
            "idempotency_key": transfer.idempotency_key,
            "sender_name": transfer.sender_name,
            "sender_iban": transfer.sender_iban,
            "sender_bic": transfer.sender_bic,
            "recipient_name": transfer.recipient_name,
            "recipient_iban": transfer.recipient_iban,
            "recipient_bic": transfer.recipient_bic,
            "amount": transfer.amount,
            "currency": transfer.currency,
            "status": transfer.status,
        },
        "sepa_xml": sepa_xml,
    }

def generate_error_template(error_message):
    return {"error": {"message": error_message, "code": "TRANSFER_ERROR"}}

# Clases base
class BaseTransferView(CreateView):
    permission_classes = [AllowAny]

    def _get_existing_record(self, model, key_value, key_field):
        return get_existing_record(model, key_value, key_field)

    def _error_response(self, message, status_code):
        return error_response(message, status_code)

    def _success_response(self, data, status_code):
        return success_response(data, status_code)

    def _generate_success_template(self, transfer, sepa_xml):
        return generate_success_template(transfer, sepa_xml)

    def _generate_error_template(self, error_message):
        return generate_error_template(error_message)

# Vistas relacionadas con SEPA2 ERROR
class SEPA3TCOM2CreateView(BaseTransferView):
    model = SEPA3
    fields = "__all__"
    template_name = "api/transfers/transfer_form.html"

    def get_queryset(self):
        return SEPA3.objects.filter(active=True)
    
    @swagger_auto_schema(operation_description="Create a transfer", request_body=SEPA3Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return self._error_response(f"Idempotency-Key header is required", status.HTTP_400_BAD_REQUEST)

        existing_transfer = self._get_existing_record(Transfer, idempotency_key, "idempotency_key")
        if existing_transfer:
            return self._success_response({"message": "Duplicate transfer", "transfer_id": existing_transfer.id}, status.HTTP_200_OK)

        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transfer_data = serializer.validated_data
        bank = request.data.get("bank")

        try:
            response = self.process_bank_transfer(bank, transfer_data, idempotency_key)
            if "error" in response:
                logger.warning(f"Error en la transferencia: {response['error']}")
                return self._error_response(self._generate_error_template(response['error']), status.HTTP_400_BAD_REQUEST)

            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            # Generar SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transfer)
                return self._success_response(self._generate_success_template(transfer, sepa_xml), status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                return self._error_response(self._generate_error_template("Error generando SEPA XML"), status.HTTP_500_INTERNAL_SERVER_ERROR)

        except APIException as e:
            logger.error(f"Error en la transferencia: {str(e)}")
            return self._error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            raise APIException("Error inesperado en la transferencia bancaria.")

    def process_bank_transfer(self, bank, transfer_data, idempotency_key):
        transfer_functions = {
            "memo": memo_bank_transfer,
            "deutsche": deutsche_bank_transfer,
        }
        if bank not in transfer_functions:
            raise APIException("Invalid bank selection")

        try:
            return transfer_functions[bank](
                transfer_data["sender_name"], 
                transfer_data["sender_iban"], 
                transfer_data["sender_bic"], 
                transfer_data["recipient_name"],
                transfer_data["recipient_iban"],
                transfer_data["recipient_bic"],
                transfer_data["amount"], 
                transfer_data["currency"], 
                idempotency_key
            )
        except Exception as e:
            logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
            raise APIException("Error procesando la transferencia bancaria.")
        
    def get_html_form_template(self):
        """Genera una plantilla HTML para ingresar datos de transferencia desde un archivo."""
        template_path = os.path.join("api/extras", "transfer_form.html")
        return render_to_string(template_path)

# HTML
class SEPA3COM2CreateView(BaseTransferView):
    model = SEPA3
    fields = "__all__"
    template_name = "api/transfers/transfer_form.html"

    @swagger_auto_schema(operation_description="Create a SEPA transfer", request_body=SEPA3Serializer)
    def post(self, request):
        IDEMPOTENCY_HEADER = "idempotency_key"
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return self._error_response(f"{IDEMPOTENCY_HEADER} header is required", status.HTTP_400_BAD_REQUEST)

        existing_transaction = self._get_existing_record(SEPA2, idempotency_key, "transaction_id")
        if existing_transaction:
            return self._success_response({"message": "Duplicate SEPA transfer", "transaction_id": existing_transaction.id}, status.HTTP_200_OK)

        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transaction = serializer.save()
        try:
            sepa_xml = generate_sepa_xml(transaction)
            return self._success_response({"sepa_xml": sepa_xml, "transaction": serializer.data}, status.HTTP_201_CREATED)
        except Exception as e:
            logger.critical(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            raise APIException("Unexpected error during SEPA transfer.")

    def process_bank_transfer(self, bank, transfer_data, idempotency_key):
        transfer_functions = {
            "deutsche": deutsche_bank_transfer,
        }
        if bank not in transfer_functions:
            raise APIException("Invalid bank selection")

        try:
            return transfer_functions[bank](
                transfer_data["sender_name"], 
                transfer_data["sender_iban"], 
                transfer_data["sender_bic"], 
                transfer_data["recipient_name"],
                transfer_data["recipient_iban"],
                transfer_data["recipient_bic"],
                transfer_data["amount"], 
                transfer_data["currency"], 
                idempotency_key
            )
        except Exception as e:
            logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
            raise APIException("Error procesando la transferencia bancaria.")

    def get_html_form_template(self):
        """Genera una plantilla HTML para ingresar datos de transferencia desde un archivo."""
        template_path = os.path.join("api/extras", "transfer_form.html")
        return render_to_string(template_path)

# Vistas basadas en APIView ERROR
class SEPA3COM2APIView(APIView):
    permission_classes = [AllowAny]
    model = SEPA3
    fields = "__all__"
    
    @swagger_auto_schema(operation_description="Create a transfer", request_body=SEPA3Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)

        existing_transfer = SEPA3.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transfer:
            return Response({"message": "Duplicate transfer", "transfer_id": existing_transfer.id}, status=status.HTTP_200_OK)

        serializer = SEPA3Serializer(data=request.data)
        if serializer.is_valid():
            transfer_data = serializer.validated_data
            bank = request.data.get("bank")

            try:
                if bank == "memo":
                    response = memo_bank_transfer(
                        transfer_data["sender_name"], 
                        transfer_data["sender_iban"], 
                        transfer_data["sender_bic"], 
                        transfer_data["recipient_name"],
                        transfer_data["recipient_iban"],
                        transfer_data["recipient_bic"],
                        transfer_data["amount"], 
                        transfer_data["currency"], 
                        idempotency_key
                    )
                elif bank == "deutsche":
                    response = deutsche_bank_transfer(
                        transfer_data["sender_name"], 
                        transfer_data["sender_iban"], 
                        transfer_data["sender_bic"], 
                        transfer_data["recipient_name"],
                        transfer_data["recipient_iban"],
                        transfer_data["recipient_bic"],
                        transfer_data["amount"], 
                        transfer_data["currency"], 
                        idempotency_key
                    )
                else:
                    return Response({"error": "Invalid bank selection"}, status=status.HTTP_400_BAD_REQUEST)

                if "error" in response:
                    logger.warning(f"Error en la transferencia: {response['error']}")
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

                serializer.save(idempotency_key=idempotency_key, status="ACCP")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
                raise APIException("Error inesperado en la transferencia bancaria.")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        transactions = SEPA3.objects.all()
        serializer = SEPA3Serializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ERROR
class SEPA3COM2List(APIView):
    permission_classes = [AllowAny]
    model = SEPA3
    fields = "__all__"

    @swagger_auto_schema(operation_description="Create a transaction", request_body=SEPA3Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar transacción existente por idempotency_key
        existing_transaction = SEPA3.objects.filter(idempotency_key=idempotency_key).first()
        
        if existing_transaction:
            return Response({"message": "Duplicate transaction", "transaction_id": existing_transaction.id}, status=status.HTTP_200_OK)
        
        # Crear nueva transacción
        serializer = SEPA3Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(idempotency_key=idempotency_key)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(operation_description="List transactions")
    def get(self, request):
        transactions = SEPA3.objects.all()
        serializer = SEPA3Serializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
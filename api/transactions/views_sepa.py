from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import APIException
from drf_yasg.utils import swagger_auto_schema
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from api.transactions.serializers import SEPASerializer
from api.transactions.models import SEPA
from api.transactions.forms import SEPAForm
from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from api.core.services import generate_sepa_xml
import logging
import os

from api.transfers.forms import SEPA2Form
from api.transfers.models import SEPA2
from api.transfers.serializers import SEPA2Serializer

logger = logging.getLogger("bank_services")

class BaseSEPAView(APIView):
    #permission_classes = [IsAllowed]

    def _get_existing_record(self, model, key_value, key_field):
        """Helper to retrieve an existing record by a unique key."""
        return model.objects.filter(**{key_field: key_value}).first()

    def _response(self, data, status_code):
        """Unified response method for success and error."""
        return Response(data, status=status_code)

    def _generate_template(self, SEPA2, sepa_xml=None, error_message=None):
        """Generates a response template for success or error."""
        if error_message:
            return {"error": {"message": error_message, "code": "TRANSFER_ERROR"}}
        return {
            "transfer": {
                "transaction_id": SEPA2.transaction_id,
                "reference": SEPA2.reference,
                "idempotency_key": SEPA2.idempotency_key,
                "amount": SEPA2.amount,
                "currency": SEPA2.currency,
                "transfer_type": SEPA2.transfer_type,
                "sepa_xml": sepa_xml,
            }
        }

class SEPATRSEPAView(BaseSEPAView):
    model = SEPA2
    fields = "__all__"
    template_name = "api/SEPA/transfer_form.html"
    
    @swagger_auto_schema(operation_description="Create a SEPA", request_body=SEPA2Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return self._response({"error": "Idempotency-Key header is required"}, status.HTTP_400_BAD_REQUEST)

        existing_transfer = self._get_existing_record(SEPA2, idempotency_key, "idempotency_key")
        if existing_transfer:
            return self._response(
                {"message": "Duplicate SEPA", "transfer_id": existing_transfer.id}, status.HTTP_200_OK
            )

        serializer = SEPA2Serializer(data=request.data)
        if not serializer.is_valid():
            return self._response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transfer_data = serializer.validated_data
        bank = request.data.get("bank")

        try:
            response = self._process_bank_transfer(bank, transfer_data, idempotency_key)
            if "error" in response:
                logger.warning(f"Error en la transferencia: {response['error']}")
                return self._response(self._generate_template(None, error_message=response['error']), status.HTTP_400_BAD_REQUEST)

            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            try:
                sepa_xml = generate_sepa_xml(transfer)
                return self._response(self._generate_template(transfer, sepa_xml), status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                return self._response(self._generate_template(None, error_message="Error generando SEPA XML"), status.HTTP_500_INTERNAL_SERVER_ERROR)

        except APIException as e:
            logger.error(f"Error en la transferencia: {str(e)}")
            return self._response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            raise APIException("Error inesperado en la transferencia bancaria.")

    def _process_bank_transfer(self, bank, transfer_data, idempotency_key):
        transfer_functions = {
            "memo": memo_bank_transfer,
            "deutsche": deutsche_bank_transfer,
        }
        if bank not in transfer_functions:
            raise APIException("Invalid bank selection")

        try:
            return transfer_functions[bank](
                transfer_data["source_account"], transfer_data["destination_account"],
                transfer_data["amount"], transfer_data["currency"], idempotency_key
            )
        except Exception as e:
            logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
            raise APIException("Error procesando la transferencia bancaria.")
    
    def get_success_url(self):
        return reverse_lazy('transfer_list')    


class TransferTRSEPAListView(ListView):
    model = SEPA2
    template_name = "api/SEPA/transfer_list.html"
    context_object_name = "transfers"


class TransferTRSEPACreateView(CreateView):
    model = SEPA2
    form_class = SEPA2Form
    template_name = "api/SEPA/transfer_form.html"
    
    def get_success_url(self):
        return reverse_lazy('transfer_list')


class TransferTRSEPAUpdateView(UpdateView):
    model = SEPA2
    form_class = SEPA2Form
    template_name = "api/SEPA/transfer_form.html"
    success_url = reverse_lazy('transfer_list')  # Redirige a la lista de transferencias


class TransferTRSEPADeleteView(DeleteView):
    model = SEPA2
    template_name = "api/SEPA/transfer_confirm_delete.html"
    success_url = reverse_lazy("transfer_list")


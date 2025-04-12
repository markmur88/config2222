import logging
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from config import settings
from config import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from drf_yasg.utils import swagger_auto_schema
from api.transfers.models import SEPA3
from api.transfers.serializers import SEPA3Serializer
from api.transfers.forms import SEPA3Form
from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from api.core.services import generate_sepa_xml
from django.views.generic.edit import CreateView

logger = logging.getLogger("bank_services")

# Constantes
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"

from rest_framework.renderers import JSONRenderer
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

def process_bank_transfer(bank, transfer_data, idempotency_key):
    transfer_functions = {
        "memo": memo_bank_transfer,
        "deutsche": deutsche_bank_transfer,
    }
    if bank not in transfer_functions:
        raise APIException("Banco seleccionado no es válido")
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

# Views basadas en APIView
class TransferALLCreateView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Create a transfer", request_body=SEPA3Serializer)
    def post(self, request):
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return error_response(f"{IDEMPOTENCY_HEADER} header is required", status.HTTP_400_BAD_REQUEST)

        existing_transfer = get_existing_record(SEPA3, idempotency_key, "idempotency_key")
        if existing_transfer:
            return success_response(
                {"message": "Duplicate transfer", "transfer_id": existing_transfer.id}, status.HTTP_200_OK
            )

        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        if not bank:
            return error_response("El campo 'bank' es obligatorio", status.HTTP_400_BAD_REQUEST)

        try:
            response = process_bank_transfer(bank, transfer_data, idempotency_key)
            if ERROR_KEY in response:
                logger.warning(f"Error en la transferencia: {response[ERROR_KEY]}")
                return error_response(response[ERROR_KEY], status.HTTP_400_BAD_REQUEST)

            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            try:
                sepa_xml = generate_sepa_xml(transfer)
                
                # Guardar una copia del SEPA XML en el directorio media
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return success_response({"transfer": serializer.data, "sepa_xml": sepa_xml}, status.HTTP_201_CREATED)
            except ValueError as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                return error_response(str(e), status.HTTP_400_BAD_REQUEST)

        except APIException as e:
            logger.error(f"Error en la transferencia: {str(e)}")
            return error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            raise APIException("Error inesperado en la transferencia bancaria.")

# Views basadas en generics
class TransferALLList(generics.ListCreateAPIView):
    queryset = SEPA3.objects.all()
    serializer_class = SEPA3Serializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        if not bank:
            return error_response("El campo 'bank' es obligatorio", status.HTTP_400_BAD_REQUEST)

        try:
            response = process_bank_transfer(bank, transfer_data, None)  # Sin idempotency_key
            if ERROR_KEY in response:
                logger.warning(f"Error en la transferencia: {response[ERROR_KEY]}")
                return error_response(response[ERROR_KEY], status.HTTP_400_BAD_REQUEST)

            transfer = serializer.save(status="ACCP")
            try:
                sepa_xml = generate_sepa_xml(transfer)
                
                # Guardar una copia del SEPA XML en el directorio media
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return success_response({"transfer": serializer.data, "sepa_xml": sepa_xml}, status.HTTP_201_CREATED)
            except ValueError as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                return error_response(str(e), status.HTTP_400_BAD_REQUEST)

        except APIException as e:
            logger.error(f"Error en la transferencia: {str(e)}")
            return error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            raise APIException("Error inesperado en la transferencia bancaria.")


class TransferALLDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SEPA3.objects.all()
    serializer_class = SEPA3Serializer

# Views basadas en plantillas
def transferALL_create_view(request):
    if request.method == 'POST':
        form = SEPA3Form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('transfer_list'))
    else:
        form = SEPA3Form()
    return render(request, 'api/transfers/transfer_form.html', {'form': form})

def transferALL_update_view(request, pk):
    transfer = get_object_or_404(SEPA3, pk=pk)
    if request.method == 'POST':
        form = SEPA3Form(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('transfer_detail', args=[pk]))
    else:
        form = SEPA3Form(instance=transfer)
    return render(request, 'api/transfers/transfer_form.html', {'form': form})

def transferALL_delete_view(request, pk):
    transfer = get_object_or_404(SEPA3, pk=pk)
    if request.method == 'POST':
        transfer.delete()
        return redirect('transfer_list')
    return render(request, 'api/transfers/transfer_confirm_delete.html', {'transfer': transfer})

class transferAllCV(CreateView):
    model = SEPA3
    form_class = SEPA3Form
    template_name = 'api/transfers/transfer_form.html'
    success_url = reverse_lazy('transfer_list')

    def form_valid(self, form):
        idempotency_key = self.request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            messages.error(self.request, f"{IDEMPOTENCY_HEADER} header is required")
            return self.form_invalid(form)

        existing_transfer = get_existing_record(SEPA3, idempotency_key, "idempotency_key")
        if existing_transfer:
            messages.info(self.request, "Duplicate transfer detected.")
            return HttpResponseRedirect(self.success_url)

        try:
            transfer = form.save(commit=False)
            transfer.idempotency_key = idempotency_key
            transfer.status = "ACCP"
            transfer.save()

            try:
                sepa_xml = generate_sepa_xml(transfer)
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                messages.success(self.request, "Transfer created successfully.")
                return HttpResponseRedirect(reverse('transfer_list'))  # Redirigir al listado
            except ValueError as e:
                logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
                messages.error(self.request, f"Error generando SEPA XML: {str(e)}")
                transfer.delete()
                return self.form_invalid(form)

        except Exception as e:
            logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
            messages.error(self.request, "Error inesperado en la transferencia bancaria.")
            return self.form_invalid(form)

        return super().form_valid(form)
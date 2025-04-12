import logging
import os
from pyexpat.errors import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
import requests
import xml.etree.ElementTree as ET
import uuid

from config import settings
from datetime import datetime
from django.core.exceptions import ImproperlyConfigured

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import APIException
from rest_framework.decorators import api_view

from drf_yasg.utils import swagger_auto_schema
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string

from api.transfers.forms import SEPA2Form
from api.transfers.models import SEPA2
from api.transfers.serializers import SEPA2Serializer

logger = logging.getLogger("bank_services")

# Constantes para cadenas repetidas
ERROR_KEY = "error"
AMOUNT_KEY = "amount"
CURRENCY_KEY = "currency"
IDEMPOTENCY_HEADER = "Idempotency-Key"

def generate_sepa_xml(transaction):
    """
    Genera un XML SEPA (ISO 20022) para la transferencia.

    Args:
        transaction: Objeto con los datos de la transacción.

    Returns:
        str: XML generado como cadena.

    Raises:
        ValueError: Si faltan datos requeridos en la transacción.
    """
    required_fields = ["sender_name", "sender_iban", "execution_date", "amount"]
    for field in required_fields:
        if not getattr(transaction, field, None):
            raise ValueError(f"El campo {field} es requerido para generar el SEPA XML.")

    # Crear el documento XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")

    # Información del grupo de pagos
    GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
    #ET.SubElement(GrpHdr, "MsgId").text = str(uuid.uuid4())  # ID único del mensaje
    ET.SubElement(GrpHdr, "MsgId").text = str(transaction.reference)  # ID único del mensaje
    #ET.SubElement(GrpHdr, "CreDtTm").text = datetime.utcnow().isoformat()
    ET.SubElement(GrpHdr, "CreDtTm").text = transaction.request_date.isoformat()
    ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
    ET.SubElement(GrpHdr, "CtrlSum").text = str(transaction.amount)
    InitgPty = ET.SubElement(GrpHdr, "InitgPty")
    #ET.SubElement(InitgPty, "Nm").text = transaction.sender_name
    ET.SubElement(InitgPty, "Nm").text = transaction.account.name

    # Información de la transacción
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    #ET.SubElement(PmtInf, "PmtInfId").text = str(uuid.uuid4())
    ET.SubElement(PmtInf, "PmtInfId").text = str(transaction.transaction_id)
    ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transferencia
    ET.SubElement(PmtInf, "BtchBookg").text = "false"
    ET.SubElement(PmtInf, "NbOfTxs").text = "1"
    ET.SubElement(PmtInf, "CtrlSum").text = str(transaction.amount)
    PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
    SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
    ET.SubElement(SvcLvl, "Cd").text = "SEPA"
    ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
    ReqdExctnDt.text = transaction.execution_date.strftime("%Y-%m-%d")

    # Datos del ordenante
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    #ET.SubElement(Dbtr, "Nm").text = transaction.sender_name
    ET.SubElement(Dbtr, "Nm").text = transaction.account.name
    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    Id = ET.SubElement(DbtrAcct, "Id")
    #ET.SubElement(Id, "IBAN").text = transaction.sender_iban
    ET.SubElement(Id, "IBAN").text = transaction.account.iban.iban
    DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
    FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
    #ET.SubElement(FinInstnId, "BIC").text = transaction.sender_bic
    ET.SubElement(FinInstnId, "BIC").text = transaction.account.iban.bic

    # Datos del beneficiario
    CdtTrfTxInf = ET.SubElement(PmtInf, "CdtTrfTxInf")
    PmtId = ET.SubElement(CdtTrfTxInf, "PmtId")
    #ET.SubElement(PmtId, "EndToEndId").text = transaction.reference
    ET.SubElement(PmtId, "EndToEndId").text = transaction.end_to_end_id
    Amt = ET.SubElement(CdtTrfTxInf, "Amt")
    ET.SubElement(Amt, "InstdAmt", Ccy=transaction.currency).text = str(transaction.amount)
    CdtrAgt = ET.SubElement(CdtTrfTxInf, "CdtrAgt")
    FinInstnId = ET.SubElement(CdtrAgt, "FinInstnId")
    #ET.SubElement(FinInstnId, "BIC").text = transaction.recipient_bic
    ET.SubElement(FinInstnId, "BIC").text = transaction.beneficiary_name.iban.bic
    Cdtr = ET.SubElement(CdtTrfTxInf, "Cdtr")
    #ET.SubElement(Cdtr, "Nm").text = transaction.recipient_name
    ET.SubElement(Cdtr, "Nm").text = transaction.beneficiary_name.name
    CdtrAcct = ET.SubElement(CdtTrfTxInf, "CdtrAcct")
    Id = ET.SubElement(CdtrAcct, "Id")
    #ET.SubElement(Id, "IBAN").text = transaction.recipient_iban
    ET.SubElement(Id, "IBAN").text = transaction.beneficiary_name.iban.iban
    RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
    #ET.SubElement(RmtInf, "Ustrd").text = transaction.unstructured_remittance_info
    ET.SubElement(RmtInf, "Ustrd").text = transaction.internal_note

    # Generar el XML
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return xml_string

def get_deutsche_bank_token():
    """Obtiene el token de Deutsche Bank."""
    url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.DEUTSCHE_BANK_CLIENT_ID,
        "client_secret": settings.DEUTSCHE_BANK_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank Token: {e}, Response: {response.text}")
        return {ERROR_KEY: "Error al obtener el token de Deutsche Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank Token: {e}")
        return {ERROR_KEY: "No se pudo conectar con Deutsche Bank"}

def deutsche_bank_transfer(source_account, destination_account, amount, currency, idempotency_key):
    url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
    headers = {
        "Authorization": f"Bearer {get_deutsche_bank_token()['access_token']}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key
    }
    payload = {
        "source_account": source_account,
        "destination_account": destination_account,
        "amount": str(amount),
        "currency": currency
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza un error si el status code no es 2xx
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": "Error en Deutsche Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": "No se pudo conectar con Deutsche Bank"}

def get_existing_record(model, key_value, key_field):
    #"""Helper to retrieve an existing record by a unique key."""
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()

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

def generate_success_template(transfer, sepa_xml):
    #"""Genera una plantilla de respuesta exitosa para una transferencia."""
    return {
        "transfer": {
            "id": transfer.id,
            "source_account": transfer.source_account,
            "destination_account": transfer.destination_account,
            "amount": transfer.amount,
            "currency": transfer.currency,
            "status": transfer.status,
        },
        "sepa_xml": sepa_xml,
    }

def generate_error_template(error_message):
    #"""Genera una plantilla de respuesta de error."""
    return {"error": {"message": error_message,"code": "TRANSFER_ERROR",}}

def process_bank_transfer(bank, transfer_data, idempotency_key):
    """Procesa una transferencia bancaria según el banco seleccionado."""
    transfer_functions = {
        # "memo": memo_bank_transfer,
        "deutsche": deutsche_bank_transfer,
    }
    if bank not in transfer_functions:
        raise APIException("Banco seleccionado no es válido")
    required_fields = ["source_account", "destination_account", AMOUNT_KEY, CURRENCY_KEY]
    for field in required_fields:
        if field not in transfer_data:
            raise APIException(f"Falta el campo requerido: {field}")
    try:
        return transfer_functions[bank](
            transfer_data["source_account"],
            transfer_data["destination_account"],
            transfer_data[AMOUNT_KEY],
            transfer_data[CURRENCY_KEY],
            idempotency_key
        )
    except Exception as e:
        logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
        raise APIException("Error procesando la transferencia bancaria.")

def get_html_form_template():
    #"""Genera una plantilla HTML para ingresar datos de transferencia desde un archivo."""
    template_path = os.path.join("api/extras", "transfer_form.html")
    return render_to_string(template_path)

def get_success_url():
    return reverse_lazy('transfer_list')

@swagger_auto_schema(method="post", operation_description="Create a transfer", request_body=SEPA2Serializer)
@api_view(["POST"])
def transfer_api_create_view(request):
    """Crea una transferencia bancaria."""
    if not request.user.is_authenticated:
        return error_response("Se requiere autenticación", status.HTTP_401_UNAUTHORIZED)
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    if not idempotency_key:
        return error_response(f"El encabezado {IDEMPOTENCY_HEADER} es obligatorio", status.HTTP_400_BAD_REQUEST)
    serializer = SEPA2Serializer(data=request.data)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    transfer_data = serializer.validated_data
    bank = request.data.get("bank")
    if not bank:
        return error_response("El campo 'bank' es obligatorio", status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic(): # type: ignore
            existing_transfer = get_existing_record(SEPA2, idempotency_key, "idempotency_key")
            if existing_transfer:
                return success_response(
                    {"message": "Transferencia duplicada", "transfer_id": existing_transfer.id},
                    status.HTTP_200_OK
                )
            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
        response = process_bank_transfer(bank, transfer_data, idempotency_key)
        if ERROR_KEY in response:
            logger.warning(f"Error en la transferencia: {response[ERROR_KEY]}")
            return error_response(generate_error_template(response[ERROR_KEY]), status.HTTP_400_BAD_REQUEST)
        try:
            sepa_xml = generate_sepa_xml(transfer)
            return success_response(generate_success_template(transfer, sepa_xml), status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
            return error_response(generate_error_template(str(e)), status.HTTP_400_BAD_REQUEST)
    except APIException as e:
        logger.error(f"Error en la transferencia: {str(e)}")
        return error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
        raise APIException("Error inesperado en la transferencia bancaria.")

@swagger_auto_schema(method="post", operation_description="Create a transfer", request_body=SEPA2Serializer)
@api_view(["POST"])
def transfer_api_view(request):
    #"""Vista principal para manejar transferencias."""
    if request.method == "POST":
        form = SEPA2Form(request.POST)
        return transfer_api_create_view(request)
    return error_response("Método no permitido", status.HTTP_405_METHOD_NOT_ALLOWED)



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

from api.transfers.models import SEPA2
from api.transfers.serializers import SEPA2Serializer

logger = logging.getLogger("bank_services")

# Constantes para cadenas repetidas
ERROR_KEY = "error"
AMOUNT_KEY = "amount"
CURRENCY_KEY = "currency"
IDEMPOTENCY_HEADER_KEY = "idempotency_key"
REFERENCE = "reference"
E2E = "end_to_end_id"
USRTI = "intenal_note"
TRANSACTION = "transaction_id"


ACCOUNT_IBAN = "account_iban"
ACCOUNT_BIC = "account_bic"
ACCOUNT_NAME = "account_name"
ACCOUNT_BANK = "account_bank"

BENEFICIARY_IBAN = "beneficiary_iban"
BENEFICIARY_BIC = "beneficiary_bic"
BENEFICIARY_NAME = "beneficiary_name"
BENEFICIARY_BANK = "beneficiary_bank"


# Mensajes de estado y error
TRANSFER_STATUS_ACCEPTED = "ACCP"
TRANSFER_DUPLICATE_MESSAGE = "Transferencia duplicada"
TRANSFER_ERROR_MESSAGE = "Error en la transferencia"
TRANSFER_UNEXPECTED_ERROR_MESSAGE = "Error inesperado en la transferencia bancaria."
DEUTSCHE_BANK_TOKEN_ERROR_MESSAGE = "No se pudo obtener el token de Deutsche Bank"
DEUTSCHE_BANK_CONNECTION_ERROR_MESSAGE = "No se pudo conectar con Deutsche Bank"

def handle_transfer_request(request):
    
    if not request.user.is_authenticated:
        return error_response("Se requiere autenticación", status.HTTP_401_UNAUTHORIZED)

    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER_KEY)
    if not idempotency_key:
        return error_response(f"El encabezado {IDEMPOTENCY_HEADER_KEY} es obligatorio", status.HTTP_400_BAD_REQUEST)

    serializer = SEPA2Serializer(data=request.data)
    if not serializer.is_valid:
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    transfer_data = serializer.validated_data
    bank = "deutsche"  # Se fuerza el uso de Deutsche Bank

    try:
        with SEPA2.objects.atomic():
            existing_transfer = get_existing_record(SEPA2, idempotency_key, "idempotency_key")
            if existing_transfer:
                return success_response(
                    {"message": TRANSFER_DUPLICATE_MESSAGE, "transfer_id": existing_transfer.transaction_id},
                    status.HTTP_200_OK
                )
            transfer = serializer.save(idempotency_key=idempotency_key, status=TRANSFER_STATUS_ACCEPTED)

        token_response = get_deutsche_bank_token()
        access_token = token_response.get("access_token")
        if not access_token:
            return error_response(DEUTSCHE_BANK_TOKEN_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)

        url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key
        }
        payload = {
            ACCOUNT_IBAN: str(transfer_data[ACCOUNT_IBAN]),
            BENEFICIARY_IBAN: str(transfer_data[BENEFICIARY_IBAN]),
            AMOUNT_KEY: str(transfer_data[AMOUNT_KEY]),
            CURRENCY_KEY: transfer_data[CURRENCY_KEY]
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        try:
            sepa_xml = generate_sepa_xml(transfer)
            return success_response(generate_success_template(transfer, sepa_xml), status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error(f"Error generando SEPA XML: {str(e)}", exc_info=True)
            return error_response(generate_error_template(str(e)), status.HTTP_400_BAD_REQUEST)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return error_response(DEUTSCHE_BANK_CONNECTION_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
    except APIException as e:
        logger.error(f"{TRANSFER_ERROR_MESSAGE}: {str(e)}")
        return error_response({ERROR_KEY: str(e)}, status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.critical(f"{TRANSFER_UNEXPECTED_ERROR_MESSAGE}: {str(e)}", exc_info=True)
        raise APIException(TRANSFER_UNEXPECTED_ERROR_MESSAGE)

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

def generate_error_template(error_message):
    return {"error": {"message": error_message, "code": "TRANSFER_ERROR"}}

def generate_success_template(transfer_data, sepa_xml):
    return {
        "transfer": {
            "id": transfer_data.transaction_id,
            "account_name": str(transfer_data[ACCOUNT_IBAN]),
            BENEFICIARY_IBAN: str(transfer_data[BENEFICIARY_IBAN]),
            AMOUNT_KEY: str(transfer_data[AMOUNT_KEY]),
            CURRENCY_KEY: transfer_data[CURRENCY_KEY],
            "status": transfer_data.status,
        },
        "sepa_xml": sepa_xml,
    }

def get_existing_record(model, key_value, key_field):
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()

def generate_sepa_xml(transfer):
    required_fields = [ACCOUNT_NAME, ACCOUNT_IBAN, ACCOUNT_BIC,"execution_date", AMOUNT_KEY, CURRENCY_KEY, BENEFICIARY_IBAN, BENEFICIARY_BIC, BENEFICIARY_NAME]
    for field in required_fields:
        if not getattr(transfer, field, None):
            raise ValueError(f"El campo {field} es requerido para generar el SEPA XML.")

    # Crear el documento XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")

    # Información del grupo de pagos
    GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
    ET.SubElement(GrpHdr, "MsgId").text = str(uuid.uuid4())  # ID único del mensaje
    ET.SubElement(GrpHdr, "CreDtTm").text = datetime.utcnow().isoformat()
    ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
    ET.SubElement(GrpHdr, "CtrlSum").text = str(getattr(transfer, AMOUNT_KEY))
    InitgPty = ET.SubElement(GrpHdr, "InitgPty")
    ET.SubElement(InitgPty, "Nm").text = transfer.ACCOUNT_NAME

    # Información de la transacción
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    #ET.SubElement(PmtInf, "PmtInfId").text = str(uuid.uuid4())
    ET.SubElement(PmtInf, "PmtInfId").text = str(getattr(transfer, AMOUNT_KEY))
    ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transferencia
    ET.SubElement(PmtInf, "BtchBookg").text = "false"
    ET.SubElement(PmtInf, "NbOfTxs").text = "1"
    ET.SubElement(PmtInf, "CtrlSum").text = str(getattr(transfer, AMOUNT_KEY))
    PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
    SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
    ET.SubElement(SvcLvl, "Cd").text = "SEPA"
    ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
    ReqdExctnDt.text = transfer.execution_date.strftime("%Y-%m-%d")

    # Datos del ordenante
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    ET.SubElement(Dbtr, "Nm").text = getattr(transfer, ACCOUNT_NAME, "")
    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    Id = ET.SubElement(DbtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = str(getattr(transfer, ACCOUNT_IBAN, ""))
    DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
    FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = getattr(transfer, ACCOUNT_BIC, "")

    # Datos del beneficiario
    CdtTrfTxInf = ET.SubElement(PmtInf, "CdtTrfTxInf")
    PmtId = ET.SubElement(CdtTrfTxInf, "PmtId")
    ET.SubElement(PmtId, "EndToEndId").text = getattr(transfer, E2E, "")
    Amt = ET.SubElement(CdtTrfTxInf, "Amt")
    ET.SubElement(Amt, "InstdAmt", Ccy=getattr(transfer, CURRENCY_KEY, "")).text = str(getattr(transfer, AMOUNT_KEY, ""))
    CdtrAgt = ET.SubElement(CdtTrfTxInf, "CdtrAgt")
    FinInstnId = ET.SubElement(CdtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = getattr(transfer, BENEFICIARY_BIC, "")
    Cdtr = ET.SubElement(CdtTrfTxInf, "Cdtr")
    ET.SubElement(Cdtr, "Nm").text = getattr(transfer, BENEFICIARY_NAME, "")
    CdtrAcct = ET.SubElement(CdtTrfTxInf, "CdtrAcct")
    Id = ET.SubElement(CdtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = str(getattr(transfer, BENEFICIARY_IBAN, ""))
    RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
    ET.SubElement(RmtInf, "Ustrd").text = getattr(transfer, "unstructured_remittance_info", "")

    # Generar el XML
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return xml_string

def get_deutsche_bank_token():
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

def process_transfer(transfer_data):
    token_response = get_deutsche_bank_token()
    access_token = token_response.get("access_token")
    if not access_token:
        return {ERROR_KEY: DEUTSCHE_BANK_TOKEN_ERROR_MESSAGE}

    url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Idempotency-Key": str(transfer_data[IDEMPOTENCY_HEADER_KEY])
    }
    payload = {
        ACCOUNT_IBAN: str(transfer_data[ACCOUNT_IBAN]),
        BENEFICIARY_IBAN: str(transfer_data[BENEFICIARY_IBAN]),
        AMOUNT_KEY: str(transfer_data[AMOUNT_KEY]),
        CURRENCY_KEY: transfer_data[CURRENCY_KEY],
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {ERROR_KEY: "Error en Deutsche Bank"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {ERROR_KEY: DEUTSCHE_BANK_CONNECTION_ERROR_MESSAGE}

def get_html_form_template():
    template_path = os.path.join("api/extras", "transfer_form.html")
    return render_to_string(template_path)

def get_success_url():
    return reverse_lazy('transfer_list')

@swagger_auto_schema(method="post", operation_description="Create a transfer", request_body=SEPA2Serializer)
@api_view(["POST"])
def transfer_api_copy_view(request):
    if request.method == "POST":
        return handle_transfer_request(request)
    return error_response("Método no permitido", status.HTTP_405_METHOD_NOT_ALLOWED)



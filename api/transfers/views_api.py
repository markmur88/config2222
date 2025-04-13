"""
API views for the Transfers application.

This module provides API endpoints for creating and managing bank transfers,
including SEPA XML generation and integration with banking services.
"""
import logging
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, Optional, Union

from django.conf import settings  # Fixed import
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

import requests
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.transfers.forms import SEPA2Form
from api.transfers.models import SEPA2
from api.transfers.serializers import SEPA2Serializer


# Configure logger
logger = logging.getLogger("bank_services")

# Constants
ERROR_KEY = "error"
AMOUNT_KEY = "amount"
CURRENCY_KEY = "currency"
IDEMPOTENCY_HEADER = "Idempotency-Key"


def generate_sepa_xml(transaction: SEPA2) -> str:
    """
    Generate a SEPA (ISO 20022) XML for the transfer.
    
    Args:
        transaction: Object containing transaction data
        
    Returns:
        str: Generated XML as a string
        
    Raises:
        ValueError: If required fields are missing from the transaction
    """
    # Check required fields
    required_fields = {
        "account": "Account",
        "beneficiary_name": "Beneficiary name",
        "execution_date": "Execution date",
        "amount": "Amount"
    }
    
    for field, display_name in required_fields.items():
        if not hasattr(transaction, field) or not getattr(transaction, field):
            raise ValueError(_(f"The field {display_name} is required to generate SEPA XML."))
    
    # Create XML document
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")
    
    # Payment group information
    GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
    ET.SubElement(GrpHdr, "MsgId").text = str(transaction.reference)  # Unique message ID
    ET.SubElement(GrpHdr, "CreDtTm").text = transaction.request_date.isoformat()
    ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
    ET.SubElement(GrpHdr, "CtrlSum").text = str(transaction.amount)
    
    InitgPty = ET.SubElement(GrpHdr, "InitgPty")
    ET.SubElement(InitgPty, "Nm").text = transaction.account.name
    
    # Transaction information
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    ET.SubElement(PmtInf, "PmtInfId").text = str(transaction.custom_id)  # Use custom_id as transaction ID
    ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transfer
    ET.SubElement(PmtInf, "BtchBookg").text = "false"
    ET.SubElement(PmtInf, "NbOfTxs").text = "1"
    ET.SubElement(PmtInf, "CtrlSum").text = str(transaction.amount)
    
    PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
    SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
    ET.SubElement(SvcLvl, "Cd").text = "SEPA"
    
    # Execution date
    ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
    ReqdExctnDt.text = transaction.execution_date.strftime("%Y-%m-%d")
    
    # Debtor (sender) information
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    ET.SubElement(Dbtr, "Nm").text = transaction.account.name
    
    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    Id = ET.SubElement(DbtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = transaction.account.iban.iban
    
    DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
    FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = transaction.account.iban.bic
    
    # Creditor (recipient) information
    CdtTrfTxInf = ET.SubElement(PmtInf, "CdtTrfTxInf")
    
    PmtId = ET.SubElement(CdtTrfTxInf, "PmtId")
    ET.SubElement(PmtId, "EndToEndId").text = str(transaction.end_to_end_id)
    
    Amt = ET.SubElement(CdtTrfTxInf, "Amt")
    ET.SubElement(Amt, "InstdAmt", Ccy=transaction.currency).text = str(transaction.amount)
    
    CdtrAgt = ET.SubElement(CdtTrfTxInf, "CdtrAgt")
    FinInstnId = ET.SubElement(CdtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = transaction.beneficiary_name.iban.bic
    
    Cdtr = ET.SubElement(CdtTrfTxInf, "Cdtr")
    ET.SubElement(Cdtr, "Nm").text = transaction.beneficiary_name.name
    
    CdtrAcct = ET.SubElement(CdtTrfTxInf, "CdtrAcct")
    Id = ET.SubElement(CdtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = transaction.beneficiary_name.iban.iban
    
    # Remittance information
    RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
    ET.SubElement(RmtInf, "Ustrd").text = transaction.internal_note or ""
    
    # Generate the XML string
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return xml_string


def get_deutsche_bank_token() -> Dict[str, Any]:
    """
    Get the authentication token from Deutsche Bank.
    
    Returns:
        Dict[str, Any]: Token data or error information
    """
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
        logger.error(f"HTTPError in Deutsche Bank Token: {e}, Response: {response.text}")
        return {ERROR_KEY: _("Error obtaining Deutsche Bank token")}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank Token: {e}")
        return {ERROR_KEY: _("Could not connect to Deutsche Bank")}


def deutsche_bank_transfer(
    source_account: str, 
    destination_account: str, 
    amount: float, 
    currency: str, 
    idempotency_key: str
) -> Dict[str, Any]:
    """
    Execute a transfer via Deutsche Bank API.
    
    Args:
        source_account: Source account identifier
        destination_account: Destination account identifier
        amount: Transfer amount
        currency: Currency code
        idempotency_key: Unique key to prevent duplicates
        
    Returns:
        Dict[str, Any]: Response from the bank API
    """
    url = f"{settings.DEUTSCHE_BANK_API_URL}/transfers"
    
    # Get the authentication token
    token_response = get_deutsche_bank_token()
    if ERROR_KEY in token_response:
        return token_response
    
    headers = {
        "Authorization": f"Bearer {token_response['access_token']}",
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
        response.raise_for_status()  # Raise an error for non-2xx status codes
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError in Deutsche Bank: {e}, Response: {response.text}")
        return {"error": _("Error in Deutsche Bank response")}
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error with Deutsche Bank: {e}")
        return {"error": _("Could not connect to Deutsche Bank")}


def get_existing_record(model: Any, key_value: Any, key_field: str) -> Optional[Any]:
    """
    Helper to retrieve an existing record by a unique key.
    
    Args:
        model: The model class to query
        key_value: The value to search for
        key_field: The field name to search in
        
    Returns:
        Optional[Any]: The found record or None if not found
    """
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()


def error_response(message: Any, status_code: int) -> Response:
    """
    Create a formatted error response.
    
    Args:
        message: The error message
        status_code: HTTP status code to return
        
    Returns:
        Response: Formatted API error response
    """
    response = Response({"error": message}, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response


def success_response(data: Dict[str, Any], status_code: int) -> Response:
    """
    Create a formatted success response.
    
    Args:
        data: The response data
        status_code: HTTP status code to return
        
    Returns:
        Response: Formatted API success response
    """
    response = Response(data, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response


def generate_success_template(transfer: SEPA2, sepa_xml: str) -> Dict[str, Any]:
    """
    Generate a success response template for a transfer.
    
    Args:
        transfer: The transfer object
        sepa_xml: The generated SEPA XML
        
    Returns:
        Dict[str, Any]: Formatted success data
    """
    return {
        "transfer": {
            "id": str(transfer.id),
            "account_name": transfer.account_name,
            "beneficiary_name": transfer.beneficiary_name.name if hasattr(transfer.beneficiary_name, 'name') else transfer.beneficiary_name,
            "amount": str(transfer.amount),
            "currency": transfer.currency,
            "status": transfer.status,
            "execution_date": transfer.execution_date.isoformat() if transfer.execution_date else None,
        },
        "sepa_xml": sepa_xml,
    }


def generate_error_template(error_message: str) -> Dict[str, Any]:
    """
    Generate an error response template.
    
    Args:
        error_message: The error message
        
    Returns:
        Dict[str, Any]: Formatted error data
    """
    return {
        "error": {
            "message": error_message,
            "code": "TRANSFER_ERROR",
        }
    }


def process_bank_transfer(bank: str, transfer_data: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
    """
    Process a bank transfer with the specified bank.
    
    Args:
        bank: The bank to use for the transfer
        transfer_data: The transfer data
        idempotency_key: The idempotency key
        
    Returns:
        Dict[str, Any]: Response from the bank
        
    Raises:
        APIException: If the bank selection is invalid or transfer fails
    """
    transfer_functions = {
        "deutsche": deutsche_bank_transfer,
    }
    
    if bank not in transfer_functions:
        raise APIException(_("Invalid bank selection"))
    
    required_fields = ["source_account", "destination_account", AMOUNT_KEY, CURRENCY_KEY]
    for field in required_fields:
        if field not in transfer_data:
            raise APIException(_(f"Missing required field: {field}"))
    
    try:
        return transfer_functions[bank](
            transfer_data["source_account"],
            transfer_data["destination_account"],
            transfer_data[AMOUNT_KEY],
            transfer_data[CURRENCY_KEY],
            idempotency_key
        )
    except Exception as e:
        logger.error(f"Error processing bank transfer: {str(e)}", exc_info=True)
        raise APIException(_("Error processing bank transfer."))


def get_html_form_template() -> str:
    """
    Generate an HTML template for entering transfer data from a file.
    
    Returns:
        str: The rendered HTML template
    """
    template_path = os.path.join("api/extras", "transfer_form.html")
    return render_to_string(template_path)


def get_success_url() -> str:
    """
    Get the URL to redirect to after a successful transfer.
    
    Returns:
        str: URL for redirection
    """
    return reverse_lazy('transfer_list')


@swagger_auto_schema(
    method="post",
    operation_description="Create a transfer",
    request_body=SEPA2Serializer,
    responses={201: SEPA2Serializer()}
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer_api_create_view(request: Request) -> Response:
    """
    Create a bank transfer.
    
    Args:
        request: The HTTP request
        
    Returns:
        Response: Result of the transfer creation
    """
    # Check for idempotency key
    idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
    if not idempotency_key:
        return error_response(
            _(f"The {IDEMPOTENCY_HEADER} header is required"),
            status.HTTP_400_BAD_REQUEST
        )
    
    # Validate input data
    serializer = SEPA2Serializer(data=request.data)
    if not serializer.is_valid():
        return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
    transfer_data = serializer.validated_data
    bank = request.data.get("bank")
    
    if not bank:
        return error_response(_("The 'bank' field is required"), status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Check for existing transfer with the same idempotency key
            existing_transfer = get_existing_record(SEPA2, idempotency_key, "idempotency_key")
            if existing_transfer:
                return success_response(
                    {
                        "message": _("Duplicate transfer"),
                        "transfer_id": str(existing_transfer.id)
                    },
                    status.HTTP_200_OK
                )
            
            # Save the transfer
            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            # Process the bank transfer
            response = process_bank_transfer(bank, transfer_data, idempotency_key)
            
            if ERROR_KEY in response:
                logger.warning(f"Error in transfer: {response[ERROR_KEY]}")
                return error_response(
                    generate_error_template(response[ERROR_KEY]),
                    status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save XML to media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return success_response(
                    generate_success_template(transfer, sepa_xml),
                    status.HTTP_201_CREATED
                )
                
            except ValueError as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                return error_response(
                    generate_error_template(str(e)),
                    status.HTTP_400_BAD_REQUEST
                )
                
    except APIException as e:
        logger.error(f"Error in transfer: {str(e)}")
        return error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
        raise APIException(_("Unexpected error in bank transfer."))


@swagger_auto_schema(
    method="post",
    operation_description="Create a transfer",
    request_body=SEPA2Serializer,
    responses={201: SEPA2Serializer()}
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def transfer_api_view(request: Request) -> Response:
    """
    Main view for handling transfers.
    
    Args:
        request: The HTTP request
        
    Returns:
        Response: Result of transfer creation or error
    """
    if request.method == "POST":
        # Validate the form data
        form = SEPA2Form(request.data)
        
        # Delegate to the create view
        return transfer_api_create_view(request)
    
    # Method not allowed for other requests
    return error_response(_("Method not allowed"), status.HTTP_405_METHOD_NOT_ALLOWED)


class TransferAPICreateView(APIView):
    """
    API view for creating transfers.
    
    Class-based view implementation of transfer creation.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a transfer",
        request_body=SEPA2Serializer,
        responses={201: SEPA2Serializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new SEPA2 transfer.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer details or error
        """
        return transfer_api_create_view(request)


class TransferAPIView(APIView):
    """
    API view for managing transfers.
    
    Provides endpoints for listing and creating transfers.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List transfers",
        responses={200: SEPA2Serializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        """
        List all transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of transfers
        """
        transfers = SEPA2.objects.filter(created_by=request.user).order_by('-request_date')
        serializer = SEPA2Serializer(transfers, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Create a transfer",
        request_body=SEPA2Serializer,
        responses={201: SEPA2Serializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new transfer.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer details or error
        """
        return transfer_api_create_view(request)
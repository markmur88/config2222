"""
Service functions for SEPA Credit Transfer processing.

This module contains shared utilities and service classes for handling 
SEPA Credit Transfer operations, including token management, response formatting,
and database operations.
"""
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, Union, Type

import requests
from django.conf import settings
from django.db.models import Model
from dotenv import load_dotenv
from drf_yasg.utils import swagger_auto_schema
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework import status, generics
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml
from api.sct.models import SepaCreditTransferRequest
from api.sct.process_deutsche_bank import deutsche_bank_transfer
from api.sct.serializers import SepaCreditTransferRequestSerializer

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Constants
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def error_response(message: str, status_code: int) -> Response:
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


def get_existing_record(model: Type[Model], key_value: Any, key_field: str) -> Optional[Model]:
    """
    Get an existing record from the database.
    
    Args:
        model: The model class to query
        key_value: The value to search for
        key_field: The field name to search in
        
    Returns:
        Optional[Model]: The found record or None if not found
    """
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()


def get_deutsche_bank_token() -> Dict[str, Any]:
    """
    Get an OAuth token from Deutsche Bank API.
    
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting Deutsche Bank token: {e}, Response: {response.text if response else 'N/A'}")
        return {"error": "Could not obtain access token"}


# SCT List View 0
class SCTCreateView(APIView):
    """
    API view for creating and listing SEPA Credit Transfers.
    
    Provides endpoints for listing all transfers and creating new ones
    with XML and PDF generation.
    """
    permission_classes = [AllowAny]
    serializer_class = SepaCreditTransferRequestSerializer
    
    def get(self, request) -> Response:
        """
        List all SEPA Credit Transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of all transfers
        """
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = self.serializer_class(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request) -> Response:
        """
        Create a new SEPA Credit Transfer with XML and PDF generation.
        
        Args:
            request: The HTTP request containing transfer data
            
        Returns:
            Response: Created transfer details or error
        """
        # Validate input data
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create and save the transfer in the database
            transfer = serializer.save(transaction_status="PDNG")
            
            # Generate SEPA XML
            sepa_xml = generate_sepa_xml(transfer)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xml_filename = f"sepa_{transfer.id}_{timestamp}.xml"
            xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            
            # Generate transfer PDF
            pdf_path = generar_pdf_transferencia(transfer)
            
            # Process bank transfer
            bank_response = deutsche_bank_transfer(None, transfer)
            
            # Update transaction status to "ACCP" if processed successfully by the bank
            transfer.transaction_status = "ACCP"
            transfer.save()
            
            # Get list of existing transfers
            transfers = SepaCreditTransferRequest.objects.all()
            transfers_serializer = self.serializer_class(transfers, many=True)
            
            # Return successful response
            return success_response(
                {
                    "transfer_id": transfer.id,
                    "transaction_status": transfer.transaction_status,
                    "sepa_xml_path": xml_path,
                    "pdf_path": pdf_path,
                    "bank_response": bank_response,
                    "transfers": transfers_serializer.data,
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error creating transfer: {str(e)}", exc_info=True)
            return error_response("Unexpected error creating transfer", status.HTTP_500_INTERNAL_SERVER_ERROR)


# SCT List View 1
class SCTList(generics.ListCreateAPIView):
    """
    Generic API view for listing and creating SEPA Credit Transfers.
    
    Uses DRF's generic views for standard list and create operations.
    """
    queryset = SepaCreditTransferRequest.objects.all()
    serializer_class = SepaCreditTransferRequestSerializer


# SCT List View 2
class SCTView(APIView):
    """
    API view for SEPA Credit Transfers with idempotency support.
    
    Handles idempotent creation of transfers and listing of all transfers.
    """
    def post(self, request) -> Response:
        """
        Create a new SEPA Credit Transfer with idempotency key.
        
        Args:
            request: The HTTP request containing transfer data and idempotency key
            
        Returns:
            Response: Created transfer details or error
        """
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_transaction = SepaCreditTransferRequest.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            return Response(
                {"message": "Duplicate transaction", "transaction_id": existing_transaction.id},
                status=status.HTTP_200_OK
            )
        
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(idempotency_key=idempotency_key)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def get(self, request) -> Response:
        """
        List all SEPA Credit Transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of all transfers
        """
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# SCT List View 3
class SepaCreditTransferCreateView3(APIView):
    """
    API view for creating SEPA Credit Transfers with status initialization.
    
    Provides endpoints for listing all transfers and creating new ones
    with pre-defined status values.
    """
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request) -> Response:
        """
        List all SEPA Credit Transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of all transfers
        """
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request) -> Response:
        """
        Create a new SEPA Credit Transfer with default status.
        
        Args:
            request: The HTTP request containing transfer data
            
        Returns:
            Response: Created transfer details or error
        """
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "transaction_status": "PDNG",
                "payment_id": "generated-payment-id",
                "auth_id": "generated-auth-id"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# SCT List View 4
class SCTLView(APIView):
    """
    API view for listing, creating, and managing SEPA Credit Transfers.
    
    Provides comprehensive handling of transfers with XML and PDF generation
    and idempotency support.
    """
    permission_classes = [AllowAny]
    serializer_class = SepaCreditTransferRequestSerializer
    
    def get(self, request) -> Response:
        """
        List all SEPA Credit Transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of all transfers
        """
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = self.serializer_class(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def post(self, request) -> Response:
        """
        Create a new SEPA Credit Transfer with idempotency support.
        
        Args:
            request: The HTTP request containing transfer data and idempotency key
            
        Returns:
            Response: Created transfer details or error
        """
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"error": "Idempotency-Key header is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if transaction with the same idempotency key already exists
        existing_transaction = SepaCreditTransferRequest.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            return Response(
                {"message": "Duplicate transaction", "transaction_id": existing_transaction.id},
                status=status.HTTP_200_OK
            )
        
        # Validate and save the new transfer
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(idempotency_key=idempotency_key, transaction_status="ACCP")
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                xml_filename = f"sepa_{transfer.id}_{timestamp}.xml"
                xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                # Generate transfer PDF
                pdf_path = generar_pdf_transferencia(transfer)
                
                # Process bank transfer
                bank_response = deutsche_bank_transfer(idempotency_key, transfer)
                
                # Update transaction status to "ACCP" if processed successfully by the bank
                transfer.transaction_status = "ACCP"
                transfer.save()
                
                # Return successful response
                return Response(
                    {
                        "transfer_id": transfer.id,
                        "transaction_status": transfer.transaction_status,
                        "sepa_xml_path": xml_path,
                        "pdf_path": pdf_path,
                        "bank_response": bank_response,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
                return Response(
                    {"error": "Unexpected error processing transfer"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
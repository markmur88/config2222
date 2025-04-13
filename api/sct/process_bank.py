"""
Processing module for SEPA Credit Transfer transactions.

Handles the processing of bank transfers, including XML generation,
communication with bank APIs, and error handling.
"""
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
from typing import Dict, Any, Optional, Union

import requests
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from django.conf import settings

from api.sct.process_deutsche_bank import deutsche_bank_transfer
from api.sct.models import SepaCreditTransferRequest
from api.sct.serializers import SepaCreditTransferRequestSerializer
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml

from dotenv import load_dotenv
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Constants
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'


def process_bank_transfer1(transfers: SepaCreditTransferRequest, idempotency_key: str) -> Dict[str, Any]:
    """
    Process a bank transfer exclusively for Deutsche Bank.
    
    Args:
        transfers: The transfer request object
        idempotency_key: Unique key to ensure idempotency
        
    Returns:
        dict: Response from the bank with transaction status
        
    Raises:
        APIException: If there's an error processing the transfer
    """
    try:
        response = deutsche_bank_transfer(idempotency_key, transfers)
        if "error" not in response:
            return {
                "transaction_status": "PDNG",
                "payment_id": str(transfers.payment_id),
                "auth_id": str(transfers.auth_id),
                "bank_response": response,
            }
        return response
    except Exception as e:
        logger.error(f"Error processing bank transfer: {str(e)}", exc_info=True)
        raise APIException("Error processing the bank transfer.")


def process_bank_transfer(idempotency_key: str, transfers: SepaCreditTransferRequest) -> Dict[str, Any]:
    """
    Process a bank transfer using a generated SEPA XML file.
    
    This function is a simplified version without extensive error handling.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: The transfer request object
        
    Returns:
        dict: Response containing success status or error information
    """
    try:
        # Generate the XML file if it doesn't exist
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        if not os.path.exists(xml_path):
            sepa_xml = generate_sepa_xml(transfers)
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
        
        # Read the XML file content
        with open(xml_path, "r") as xml_file:
            xml_content = xml_file.read()
        
        # Send the XML to the bank
        response = requests.post(
            url=settings.BANK_API_URL,
            headers={"Content-Type": "application/xml"},
            data=xml_content
        )
        
        # Check the bank's response
        if response.status_code != 200:
            return {"error": f"Error sending XML to bank: {response.text}"}
        
        # Process the bank's response (assuming it's XML)
        bank_response = response.text
        return {"success": True, "bank_response": bank_response}
    
    except Exception as e:
        logger.error(f"Error in process_bank_transfer: {str(e)}", exc_info=True)
        return {"error": str(e)}


def process_bank_transfer11(idempotency_key: str, transfers: SepaCreditTransferRequest) -> Dict[str, Any]:
    """
    Process a bank transfer using a generated SEPA XML file.
    
    This version includes comprehensive error handling and logging.
    
    Args:
        idempotency_key: Unique key to ensure idempotency
        transfers: The transfer request object
        
    Returns:
        dict: Response containing success status or error information
    """
    try:
        # XML file path
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        
        # Generate the XML file if it doesn't exist
        if not os.path.exists(xml_path):
            try:
                sepa_xml = generate_sepa_xml(transfers)
                with open(xml_path, "w", encoding="utf-8") as xml_file:
                    os.chmod(xml_path, 0o600)  # Restrictive permissions
                    xml_file.write(sepa_xml)
            except Exception as e:
                logger.error(f"Error generating or saving XML file: {str(e)}", exc_info=True)
                return {"error": "Error generating XML file"}
        
        # Read the XML file content
        try:
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
        except Exception as e:
            logger.error(f"Error reading XML file: {str(e)}", exc_info=True)
            return {"error": "Error reading XML file"}
        
        # Send the XML to the bank
        try:
            response = requests.post(
                url=settings.BANK_API_URL,
                headers={"Content-Type": "application/xml"},
                data=xml_content
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending XML to bank: {str(e)}", exc_info=True)
            return {"error": "Error sending XML to bank"}
        
        # Check the bank's response
        if response.status_code != 200:
            logger.error(f"Bank response with error: {response.text}")
            return {"error": f"Error sending XML to bank: {response.text}"}
        
        # Process the bank's response
        try:
            bank_response = response.text  # Assuming it's text or XML
            return {"success": True, "bank_response": bank_response}
        except Exception as e:
            logger.error(f"Error processing bank response: {str(e)}", exc_info=True)
            return {"error": "Error processing bank response"}
    
    except Exception as e:
        logger.error(f"Unexpected error in process_bank_transfer for idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}


class ProcessTransferView11(APIView):
    """
    API view for processing a transfer with Deutsche Bank.
    
    Provides endpoint for initiating a transfer using ProcessTransferView11.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer using the specified idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: Unique key to ensure idempotency
            
        Returns:
            Response: API response with transaction status or error
        """
        try:
            # Find the transfer by idempotency key
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            
            # Process the bank transfer
            result = process_bank_transfer1(transfer, idempotency_key)
            
            if ERROR_KEY in result:
                return Response(
                    {ERROR_KEY: result[ERROR_KEY]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate PDF receipt
            try:
                pdf_path = generar_pdf_transferencia(transfer)
                result["pdf_path"] = pdf_path
            except Exception as e:
                logger.warning(f"PDF generation failed but transfer was successful: {str(e)}")
                result["pdf_warning"] = "PDF generation failed but transfer was successful"
            
            return Response(result, status=status.HTTP_200_OK)
            
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with idempotency_key {idempotency_key} not found")
            return Response(
                {ERROR_KEY: f"Transfer with idempotency_key {idempotency_key} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response(
                {ERROR_KEY: f"Error processing transfer: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessTransferView12(APIView):
    """
    API view for processing a transfer with any bank supporting SEPA XML.
    
    Provides endpoint for initiating a transfer using ProcessTransferView12.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer using the specified idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: Unique key to ensure idempotency
            
        Returns:
            Response: API response with transaction status or error
        """
        try:
            # Find the transfer by idempotency key
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            
            # Process the bank transfer
            result = process_bank_transfer11(idempotency_key, transfer)
            
            if ERROR_KEY in result:
                return Response(
                    {ERROR_KEY: result[ERROR_KEY]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate PDF receipt
            try:
                pdf_path = generar_pdf_transferencia(transfer)
                result["pdf_path"] = pdf_path
            except Exception as e:
                logger.warning(f"PDF generation failed but transfer was successful: {str(e)}")
                result["pdf_warning"] = "PDF generation failed but transfer was successful"
            
            return Response(result, status=status.HTTP_200_OK)
            
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with idempotency_key {idempotency_key} not found")
            return Response(
                {ERROR_KEY: f"Transfer with idempotency_key {idempotency_key} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response(
                {ERROR_KEY: f"Error processing transfer: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
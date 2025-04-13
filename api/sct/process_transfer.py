"""
API views for processing SEPA Credit Transfers.

This module contains views for handling SEPA transfer processing,
including different implementations for various bank integrations.
"""
import os
import logging
from datetime import date
from typing import Dict, Any, Optional, Union
from uuid import uuid4

from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from api.sct.forms import SepaCreditTransferRequestForm
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml
from api.sct.models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from api.sct.process_bank import process_bank_transfer, process_bank_transfer1, process_bank_transfer11
from api.sct.serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer,
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)
from api.sct.services import deutsche_bank_transfer


# Configure logger
logger = logging.getLogger("bank_services")

# Constants
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = "idempotency_key"
ERROR_KEY = "error"


class ProcessTransferView1(APIView):
    """
    API view for processing transfers with basic functionality.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with processing result or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            return Response({"message": "Transfer processed successfully.", "bank_response": bank_response}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView11(APIView):
    """
    API view for processing transfers with XML generation.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer by idempotency key and generate XML file.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with processing result or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            # Generate XML file
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            
            return Response({
                "message": "Transfer processed successfully.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with idempotency_key {idempotency_key} not found.", exc_info=True)
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView2(APIView):
    """
    API view for processing transfers with XML content in response.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer by idempotency key and return XML content.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with processing result and XML content or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            # Generate XML file
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
                
            # Read XML content
            if not os.path.exists(xml_path):
                return Response({"error": "Failed to generate XML file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
            
            return Response({
                "message": "Transfer processed successfully.",
                "bank_response": bank_response,
                "xml_content": xml_content
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView3(APIView):
    """
    API view for processing transfers with creation capability.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: str) -> Response:
        """
        Process or create a transfer with the given data.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer (optional)
            
        Returns:
            Response: API response with processing result or error
        """
        idempotency_key = request.data.get("idempotency_key")
        
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                transfers = serializer.save(transaction_status="PDNG")
                idempotency_key = transfers.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(idempotency_key, transfers)
            
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            # Generate XML file
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            
            return Response({
                "message": "Transfer processed successfully.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView4(APIView):
    """
    API view for processing transfers with flexible idempotency key handling.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: Optional[str] = None) -> Response:
        """
        Process or create a transfer with flexible idempotency key handling.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer (optional)
            
        Returns:
            Response: API response with processing result or error
        """
        # Get idempotency_key from data or argument
        if not idempotency_key:
            idempotency_key = request.data.get("idempotency_key")
            
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                transfers = serializer.save(transaction_status="ACCP")
                idempotency_key = transfers.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(transfers, idempotency_key)
            
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            # Generate XML file
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            
            return Response({
                "message": "Transfer processed successfully.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView12(APIView):
    """
    API view for processing transfers with multiple processing methods.
    """
    def get(self, request, idempotency_key: str) -> Response:
        """
        Get transfer details by idempotency key.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with transfer details or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting transfer details: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error getting transfer details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key: str) -> Response:
        """
        Process a transfer using multiple processing methods.
        
        Args:
            request: The HTTP request
            idempotency_key: The idempotency key to look up the transfer
            
        Returns:
            Response: API response with processing results or error
        """
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            
            # Process with process_bank_transfer1
            bank_response_1 = process_bank_transfer1(idempotency_key, transfers)
            
            # Check if there was an error in the first processing
            if "error" in bank_response_1:
                return Response({"error": bank_response_1["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            # Process with process_bank_transfer11
            bank_response_2 = process_bank_transfer11(transfers, idempotency_key)
            
            # Check if there was an error in the second processing
            if "error" in bank_response_2:
                return Response({"error": bank_response_2["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the transfer status
            transfers.transaction_status = "ACCP"
            transfers.save()
            
            return Response({
                "message": "Transfer processed successfully.",
                "bank_response_1": bank_response_1,
                "bank_response_2": bank_response_2
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            return Response({"error": "Unexpected error processing transfer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
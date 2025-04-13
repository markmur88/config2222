"""
COM2 views for the Transfers application.

This module defines specialized views for SEPA3 transfers including
both API endpoints and web interface routes for COM2 integration.
"""
import logging
import os
from typing import Any, Dict, Optional, Union, Type

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer, sepa_transfer
from api.core.services import generate_sepa_xml
from api.transfers.forms import SEPA2Form, SEPA3Form
from api.transfers.models import SEPA2, Transfer, SEPA3, TransferAttachment
from api.transfers.serializers import (
    SEPA3Serializer, SEPA3ListSerializer, 
    TransferAttachmentSerializer, TransferSerializer
)


# Configure logger
logger = logging.getLogger("bank_services")


# Helper functions
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


def get_existing_record(model: Type, key_value: Any, key_field: str) -> Optional[Any]:
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


def generate_success_template(transfer: SEPA3, sepa_xml: str) -> Dict[str, Any]:
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
            "idempotency_key": str(transfer.idempotency_key),
            "sender_name": transfer.sender_name,
            "sender_iban": transfer.sender_iban,
            "sender_bic": transfer.sender_bic,
            "recipient_name": transfer.recipient_name,
            "recipient_iban": transfer.recipient_iban,
            "recipient_bic": transfer.recipient_bic,
            "amount": str(transfer.amount),
            "currency": transfer.currency,
            "status": transfer.status,
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
            "code": "TRANSFER_ERROR"
        }
    }


def get_html_form_template() -> str:
    """
    Generate an HTML template for entering transfer data from a file.
    
    Returns:
        str: The rendered HTML template
    """
    template_path = os.path.join("api/transfers/templates", "transfer_form.html")
    return render_to_string(template_path)


# Base view classes
class BaseTransferView(CreateView):
    """
    Base class for transfer-related views.
    
    Provides common functionality for transfer views.
    """
    permission_classes = [IsAuthenticated]
    
    def _get_existing_record(self, model: Type, key_value: Any, key_field: str) -> Optional[Any]:
        """
        Retrieve an existing record by a unique key.
        
        Args:
            model: The model class to query
            key_value: The value to search for
            key_field: The field name to search in
            
        Returns:
            Optional[Any]: The found record or None if not found
        """
        return get_existing_record(model, key_value, key_field)
    
    def _error_response(self, message: Any, status_code: int) -> Response:
        """
        Create a formatted error response.
        
        Args:
            message: The error message
            status_code: HTTP status code to return
            
        Returns:
            Response: Formatted API error response
        """
        return error_response(message, status_code)
    
    def _success_response(self, data: Dict[str, Any], status_code: int) -> Response:
        """
        Create a formatted success response.
        
        Args:
            data: The response data
            status_code: HTTP status code to return
            
        Returns:
            Response: Formatted API success response
        """
        return success_response(data, status_code)
    
    def _generate_success_template(self, transfer: SEPA3, sepa_xml: str) -> Dict[str, Any]:
        """
        Generate a success response template for a transfer.
        
        Args:
            transfer: The transfer object
            sepa_xml: The generated SEPA XML
            
        Returns:
            Dict[str, Any]: Formatted success data
        """
        return generate_success_template(transfer, sepa_xml)
    
    def _generate_error_template(self, error_message: str) -> Dict[str, Any]:
        """
        Generate an error response template.
        
        Args:
            error_message: The error message
            
        Returns:
            Dict[str, Any]: Formatted error data
        """
        return generate_error_template(error_message)
    
    def process_bank_transfer(self, bank: str, transfer_data: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
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
            "memo": memo_bank_transfer,
            "deutsche": deutsche_bank_transfer,
        }
        
        if bank not in transfer_functions:
            raise APIException(_("Invalid bank selection"))
        
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
            logger.error(f"Error processing bank transfer: {str(e)}", exc_info=True)
            raise APIException(_("Error processing bank transfer."))


# SEPA3 Transfer views
class SEPA3TCOM2CreateView(BaseTransferView):
    """
    View for creating SEPA3 transfers via COM2 integration.
    
    Handles transfer creation with bank processing and XML generation.
    """
    model = SEPA3
    fields = "__all__"
    template_name = "api/transfers/transfer_form.html"
    
    def get_queryset(self):
        """Return active transfers only."""
        return SEPA3.objects.filter(active=True)
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create SEPA3 Transfer')
        return context
    
    @swagger_auto_schema(
        operation_description="Create a transfer",
        request_body=SEPA3Serializer,
        responses={201: SEPA3Serializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new SEPA3 transfer.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer details or error
        """
        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return self._error_response(
                _("Idempotency-Key header is required"),
                status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing transfer with the same idempotency key
        existing_transfer = self._get_existing_record(Transfer, idempotency_key, "idempotency_key")
        if existing_transfer:
            return self._success_response(
                {
                    "message": _("Duplicate transfer"),
                    "transfer_id": str(existing_transfer.id)
                },
                status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        
        try:
            # Process the bank transfer
            response = self.process_bank_transfer(bank, transfer_data, idempotency_key)
            
            if "error" in response:
                logger.warning(f"Error in transfer: {response['error']}")
                return self._error_response(
                    self._generate_error_template(response['error']),
                    status.HTTP_400_BAD_REQUEST
                )
            
            # Save the transfer
            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save XML to media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return self._success_response(
                    self._generate_success_template(transfer, sepa_xml),
                    status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                return self._error_response(
                    self._generate_error_template(_("Error generating SEPA XML")),
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except APIException as e:
            logger.error(f"Error in transfer: {str(e)}")
            return self._error_response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException(_("Unexpected error in bank transfer."))


class SEPA3COM2CreateView(BaseTransferView):
    """
    View for creating SEPA3 transfers with web interface.
    
    Handles transfer creation and XML generation.
    """
    model = SEPA3
    form_class = SEPA3Form
    template_name = "api/transfers/transfer_form.html"
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create SEPA3 Transfer')
        return context
    
    @swagger_auto_schema(
        operation_description="Create a SEPA transfer",
        request_body=SEPA3Serializer,
        responses={201: SEPA3Serializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new SEPA3 transfer from form data.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer details or error
        """
        IDEMPOTENCY_HEADER = "Idempotency-Key"
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        
        if not idempotency_key:
            return self._error_response(
                _(f"{IDEMPOTENCY_HEADER} header is required"),
                status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing transfer
        existing_transaction = self._get_existing_record(SEPA2, idempotency_key, "idempotency_key")
        if existing_transaction:
            return self._success_response(
                {
                    "message": _("Duplicate SEPA transfer"),
                    "transaction_id": str(existing_transaction.id)
                },
                status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        # Save the transaction
        transaction = serializer.save(idempotency_key=idempotency_key)
        
        try:
            # Generate SEPA XML
            sepa_xml = generate_sepa_xml(transaction)
            
            # Save XML to media directory
            media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transaction.id}.xml")
            with open(media_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            
            return self._success_response(
                {"sepa_xml": sepa_xml, "transaction": serializer.data},
                status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.critical(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            raise APIException(_("Unexpected error during SEPA transfer."))


class SEPA3COM2APIView(APIView):
    """
    API view for SEPA3 transfers.
    
    Provides endpoints for listing and creating SEPA3 transfers.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all transfers",
        responses={200: SEPA3ListSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        """
        List all SEPA3 transfers.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of transfers
        """
        transactions = SEPA3.objects.all().order_by('-created_at')
        serializer = SEPA3Serializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Create a transfer",
        request_body=SEPA3Serializer,
        responses={201: SEPA3Serializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new SEPA3 transfer.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer details or error
        """
        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"error": _("Idempotency-Key header is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing transfer
        existing_transfer = SEPA3.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transfer:
            return Response(
                {
                    "message": _("Duplicate transfer"),
                    "transfer_id": str(existing_transfer.id)
                },
                status=status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        
        try:
            # Process the bank transfer based on the selected bank
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
                return Response(
                    {"error": _("Invalid bank selection")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for errors in the bank response
            if "error" in response:
                logger.warning(f"Error in transfer: {response['error']}")
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
            # Save the transfer
            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            # Generate SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save XML to media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                # Include XML in response
                result = serializer.data
                result['sepa_xml'] = sepa_xml
                
                return Response(result, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                # Continue without XML
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException(_("Unexpected error in bank transfer."))


class SEPA3COM2List(ListView):
    """
    View for listing SEPA3 transfers.
    
    Provides a web interface for listing transfers.
    """
    model = SEPA3
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"
    ordering = ['-created_at']
    paginate_by = 10
    
    def get_queryset(self):
        """Filter queryset based on GET parameters."""
        queryset = super().get_queryset()
        
        # Apply filters if provided
        status_filter = self.request.GET.get('status')
        sender = self.request.GET.get('sender')
        recipient = self.request.GET.get('recipient')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if sender:
            queryset = queryset.filter(sender_name__icontains=sender)
        if recipient:
            queryset = queryset.filter(recipient_name__icontains=recipient)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA3 Transfers')
        
        # Add filter values to context
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'sender': self.request.GET.get('sender', ''),
            'recipient': self.request.GET.get('recipient', '')
        }
        
        return context


class SEPA3ViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SEPA3 transfers.
    
    Provides CRUD operations for SEPA3 transfers via API.
    """
    queryset = SEPA3.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Returns:
            Type[serializers.Serializer]: The appropriate serializer class
        """
        if self.action == 'list':
            return SEPA3ListSerializer
        return SEPA3Serializer
    
    def perform_create(self, serializer):
        """
        Create a new SEPA3 transfer.
        
        Args:
            serializer: The validated serializer
        """
        # Generate a unique idempotency key if not provided
        idempotency_key = self.request.headers.get("Idempotency-Key", None)
        
        if not idempotency_key:
            import uuid
            idempotency_key = str(uuid.uuid4())
        
        serializer.save(
            idempotency_key=idempotency_key,
            status="PDNG",
            created_by=self.request.user
        )
    
    @swagger_auto_schema(
        operation_description="Generate SEPA XML",
        responses={200: "SEPA XML content"}
    )
    def generate_xml(self, request, pk=None):
        """
        Generate SEPA XML for a transfer.
        
        Args:
            request: The HTTP request
            pk: The primary key of the transfer
            
        Returns:
            Response: SEPA XML content
        """
        transfer = self.get_object()
        
        try:
            sepa_xml = generate_sepa_xml(transfer)
            
            # Save XML to media directory
            media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
            with open(media_path, "w") as xml_file:
                xml_file.write(sepa_xml)
                
            return Response({"sepa_xml": sepa_xml})
            
        except Exception as e:
            logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            return Response(
                {"error": _("Error generating SEPA XML")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Standard transfers.
    
    Provides CRUD operations for Transfer model via API.
    """
    queryset = Transfer.objects.all().order_by('-created_at')
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter transfers for the current user."""
        queryset = super().get_queryset()
        
        # Apply filters if provided
        status_filter = self.request.query_params.get('status')
        source = self.request.query_params.get('source')
        destination = self.request.query_params.get('destination')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if source:
            queryset = queryset.filter(source_account__icontains=source)
        if destination:
            queryset = queryset.filter(destination_account__icontains=destination)
            
        return queryset
    
    def perform_create(self, serializer):
        """Create transfer with current user."""
        serializer.save(
            idempotency_key=self.request.headers.get("Idempotency-Key") or str(uuid.uuid4()),
            status="PDNG"
        )
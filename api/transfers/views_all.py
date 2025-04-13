"""
All-purpose views for the Transfers application.

This module provides comprehensive views for managing SEPA3 transfers,
including both API endpoints and web interface views.
"""
import logging
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, Optional, Union

from django.conf import settings  # Fixed import from django.conf
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView

from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from api.core.services import generate_sepa_xml
from api.transfers.forms import SEPA3Form
from api.transfers.models import SEPA3, TransferAttachment
from api.transfers.serializers import SEPA3Serializer


# Configure logger
logger = logging.getLogger("bank_services")

# Constants
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"


# Helper functions
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


def get_existing_record(model: Any, key_value: Any, key_field: str) -> Optional[Any]:
    """
    Get an existing record from the database.
    
    Args:
        model: The model class to query
        key_value: The value to search for
        key_field: The field name to search in
        
    Returns:
        Optional[Any]: The found record or None if not found
    """
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()


def process_bank_transfer(bank: str, transfer_data: Dict[str, Any], idempotency_key: Optional[str]) -> Dict[str, Any]:
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
        raise APIException("Invalid bank selection")
    
    try:
        # Generate an idempotency key if not provided
        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())
            
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
        raise APIException("Error processing bank transfer.")


# API Views based on APIView
class TransferALLCreateView(APIView):
    """
    API view for creating SEPA3 transfers.
    
    Provides an endpoint for creating transfers with idempotency support.
    """
    permission_classes = [AllowAny]
    
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
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return error_response(
                f"{IDEMPOTENCY_HEADER} header is required", 
                status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing transfer with the same idempotency key
        existing_transfer = get_existing_record(SEPA3, idempotency_key, "idempotency_key")
        if existing_transfer:
            return success_response(
                {
                    "message": "Duplicate transfer",
                    "transfer_id": str(existing_transfer.id)
                },
                status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = SEPA3Serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        
        if not bank:
            return error_response("The 'bank' field is required", status.HTTP_400_BAD_REQUEST)
        
        try:
            # Process the bank transfer
            response = process_bank_transfer(bank, transfer_data, idempotency_key)
            
            if ERROR_KEY in response:
                logger.warning(f"Error in transfer: {response[ERROR_KEY]}")
                return error_response(response[ERROR_KEY], status.HTTP_400_BAD_REQUEST)
            
            # Save the transfer
            transfer = serializer.save(idempotency_key=idempotency_key, status="ACCP")
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save a copy of the SEPA XML in the media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return success_response(
                    {"transfer": serializer.data, "sepa_xml": sepa_xml},
                    status.HTTP_201_CREATED
                )
                
            except ValueError as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                return error_response(str(e), status.HTTP_400_BAD_REQUEST)
                
        except APIException as e:
            logger.error(f"Error in transfer: {str(e)}")
            return error_response(str(e), status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException("Unexpected error in bank transfer.")


# Views based on generics
class TransferALLList(generics.ListCreateAPIView):
    """
    API view for listing and creating SEPA3 transfers.
    
    GET: List all transfers
    POST: Create a new transfer
    """
    queryset = SEPA3.objects.all().order_by('-created_at')
    serializer_class = SEPA3Serializer
    
    def get_queryset(self):
        """Filter transfers based on query parameters."""
        queryset = super().get_queryset()
        
        # Apply filters if provided
        status_filter = self.request.query_params.get('status')
        sender = self.request.query_params.get('sender')
        recipient = self.request.query_params.get('recipient')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if sender:
            queryset = queryset.filter(sender_name__icontains=sender)
        if recipient:
            queryset = queryset.filter(recipient_name__icontains=recipient)
            
        return queryset
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new SEPA3 transfer.
        
        Args:
            request: The HTTP request
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Response: Created transfer details or error
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        
        if not bank:
            return error_response("The 'bank' field is required", status.HTTP_400_BAD_REQUEST)
        
        try:
            # Process the bank transfer without idempotency key
            response = process_bank_transfer(bank, transfer_data, None)
            
            if ERROR_KEY in response:
                logger.warning(f"Error in transfer: {response[ERROR_KEY]}")
                return error_response(response[ERROR_KEY], status.HTTP_400_BAD_REQUEST)
            
            # Save the transfer
            transfer = serializer.save(status="ACCP")
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save a copy of the SEPA XML in the media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                return success_response(
                    {"transfer": serializer.data, "sepa_xml": sepa_xml},
                    status.HTTP_201_CREATED
                )
                
            except ValueError as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                return error_response(str(e), status.HTTP_400_BAD_REQUEST)
                
        except APIException as e:
            logger.error(f"Error in transfer: {str(e)}")
            return error_response(str(e), status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException("Unexpected error in bank transfer.")


class TransferALLDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a SEPA3 transfer.
    
    GET: Retrieve a transfer
    PUT/PATCH: Update a transfer
    DELETE: Delete a transfer
    """
    queryset = SEPA3.objects.all()
    serializer_class = SEPA3Serializer
    
    def perform_update(self, serializer):
        """Log updates to transfers."""
        transfer = serializer.save()
        logger.info(f"Transfer updated: {transfer.id}")
    
    def perform_destroy(self, instance):
        """Log deletions of transfers."""
        logger.info(f"Transfer deleted: {instance.id}")
        instance.delete()


# Template-based views
def transferALL_create_view(request: HttpRequest) -> HttpResponse:
    """
    View for creating a new SEPA3 transfer with a form.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered form or redirect
    """
    if request.method == 'POST':
        form = SEPA3Form(request.POST)
        if form.is_valid():
            transfer = form.save()
            messages.success(request, _("Transfer created successfully"))
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Save a copy of the SEPA XML in the media directory
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                    
                messages.info(request, _("SEPA XML generated successfully"))
                
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                messages.warning(request, _("Transfer created but XML generation failed"))
                
            return HttpResponseRedirect(reverse('transfer_list'))
        else:
            messages.error(request, _("Please correct the errors below"))
    else:
        form = SEPA3Form()
    
    return render(request, 'api/transfers/transfer_form.html', {
        'form': form,
        'title': _('Create Transfer')
    })


def transferALL_update_view(request: HttpRequest, pk: str) -> HttpResponse:
    """
    View for updating an existing SEPA3 transfer with a form.
    
    Args:
        request: The HTTP request
        pk: The primary key of the transfer
        
    Returns:
        HttpResponse: Rendered form or redirect
    """
    transfer = get_object_or_404(SEPA3, pk=pk)
    
    if request.method == 'POST':
        form = SEPA3Form(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            messages.success(request, _("Transfer updated successfully"))
            return HttpResponseRedirect(reverse('transfer_detail', args=[pk]))
        else:
            messages.error(request, _("Please correct the errors below"))
    else:
        form = SEPA3Form(instance=transfer)
    
    return render(request, 'api/transfers/transfer_form.html', {
        'form': form,
        'transfer': transfer,
        'title': _('Update Transfer')
    })


def transferALL_delete_view(request: HttpRequest, pk: str) -> HttpResponse:
    """
    View for deleting a SEPA3 transfer.
    
    Args:
        request: The HTTP request
        pk: The primary key of the transfer
        
    Returns:
        HttpResponse: Rendered confirmation or redirect
    """
    transfer = get_object_or_404(SEPA3, pk=pk)
    
    if request.method == 'POST':
        transfer.delete()
        messages.success(request, _("Transfer deleted successfully"))
        return redirect('transfer_list')
    
    return render(request, 'api/transfers/transfer_confirm_delete.html', {
        'transfer': transfer,
        'title': _('Delete Transfer')
    })


class transferAllCV(CreateView):
    """
    Class-based view for creating a SEPA3 transfer with a form.
    
    Uses Django's CreateView for form handling and rendering.
    """
    model = SEPA3
    form_class = SEPA3Form
    template_name = 'api/transfers/transfer_form.html'
    success_url = reverse_lazy('transfer_list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Transfer')
        return context
    
    def form_valid(self, form):
        """
        Handle valid form submission with idempotency check.
        
        Args:
            form: The validated form
            
        Returns:
            HttpResponse: Redirect on success or form with errors
        """
        idempotency_key = self.request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            messages.error(self.request, _(f"{IDEMPOTENCY_HEADER} header is required"))
            return self.form_invalid(form)
        
        existing_transfer = get_existing_record(SEPA3, idempotency_key, "idempotency_key")
        if existing_transfer:
            messages.info(self.request, _("Duplicate transfer detected."))
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
                
                messages.success(self.request, _("Transfer created successfully."))
                return HttpResponseRedirect(self.success_url)
                
            except ValueError as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                messages.error(self.request, _(f"Error generating SEPA XML: {str(e)}"))
                transfer.delete()
                return self.form_invalid(form)
                
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            messages.error(self.request, _("Unexpected error in bank transfer."))
            return self.form_invalid(form)
            
        return super().form_valid(form)
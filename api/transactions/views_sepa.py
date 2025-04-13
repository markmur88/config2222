"""
Views for SEPA transfers in the Transactions application.

This module defines both API endpoints and web interface views for
managing SEPA (Single Euro Payments Area) transfers.
"""
import logging
import os
from typing import Any, Dict, Optional, Type, Union

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from api.core.models import Debtor
from api.core.services import generate_sepa_xml
from api.transactions.forms import SEPAForm
from api.transactions.models import SEPA, TransactionAttachment
from api.transactions.serializers import SEPASerializer, SEPAListSerializer


# Configure logger
logger = logging.getLogger("bank_services")


class BaseSEPAView(APIView):
    """
    Base class for SEPA transfer API views.
    
    Provides common functionality for SEPA transfer API endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    def _get_existing_record(self, model: Type, key_value: Any, key_field: str) -> Optional[Any]:
        """
        Helper to retrieve an existing record by a unique key.
        
        Args:
            model: The model class to query
            key_value: The value to search for
            key_field: The field name to search in
            
        Returns:
            Optional[Any]: The found record or None if not found
        """
        return model.objects.filter(**{key_field: key_value}).first()
    
    def _response(self, data: Dict[str, Any], status_code: int) -> Response:
        """
        Unified response method for success and error.
        
        Args:
            data: The response data
            status_code: The HTTP status code
            
        Returns:
            Response: Formatted API response
        """
        return Response(data, status=status_code)
    
    def _generate_template(self, sepa: Optional[SEPA] = None, sepa_xml: Optional[str] = None, 
                          error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a response template for success or error.
        
        Args:
            sepa: The SEPA transfer object
            sepa_xml: The generated SEPA XML content
            error_message: Error message if any
            
        Returns:
            Dict[str, Any]: Response template
        """
        if error_message:
            return {"error": {"message": error_message, "code": "TRANSFER_ERROR"}}
        
        if not sepa:
            return {"error": {"message": "No transfer data provided", "code": "MISSING_DATA"}}
        
        return {
            "transfer": {
                "transaction_id": str(sepa.transaction_id),
                "reference": str(sepa.reference),
                "idempotency_key": str(sepa.idempotency_key),
                "amount": str(sepa.amount),
                "currency": sepa.currency,
                "transfer_type": sepa.transfer_type,
                "status": sepa.status,
                "sepa_xml": sepa_xml,
            }
        }


class SEPAView(BaseSEPAView):
    """
    API view for SEPA transfers.
    
    Provides endpoints for listing and creating SEPA transfers.
    """
    
    @swagger_auto_schema(
        operation_description="List SEPA transfers",
        responses={200: SEPAListSerializer(many=True)}
    )
    def get(self, request: Request) -> Response:
        """
        List all SEPA transfers with optional filtering.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of SEPA transfers
        """
        try:
            # Get transfers with optional filtering
            transfers = SEPA.objects.all().order_by('-request_date')
            
            # Apply filters if provided
            status_filter = request.query_params.get('status')
            beneficiary = request.query_params.get('beneficiary')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            if status_filter:
                transfers = transfers.filter(status=status_filter)
            if beneficiary:
                transfers = transfers.filter(beneficiary_name__name__icontains=beneficiary)
            if date_from:
                transfers = transfers.filter(request_date__gte=date_from)
            if date_to:
                transfers = transfers.filter(request_date__lte=date_to)
            
            # Serialize and return data
            serializer = SEPAListSerializer(transfers, many=True)
            return self._response(serializer.data, status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error listing SEPA transfers: {str(e)}", exc_info=True)
            return self._response(
                {"error": f"Error listing transfers: {str(e)}"},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Create a SEPA transfer",
        request_body=SEPASerializer,
        responses={201: SEPASerializer()}
    )
    def post(self, request: Request) -> Response:
        """
        Create a new SEPA transfer.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Created transfer or error
        """
        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return self._response(
                {"error": "Idempotency-Key header is required"},
                status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing transfer with the same idempotency key
        existing_transfer = self._get_existing_record(SEPA, idempotency_key, "idempotency_key")
        if existing_transfer:
            return self._response(
                {
                    "message": "Duplicate SEPA transfer",
                    "transfer_id": str(existing_transfer.transaction_id)
                },
                status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = SEPASerializer(data=request.data)
        if not serializer.is_valid():
            return self._response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank", "deutsche")  # Default to Deutsche Bank
        
        try:
            # Process the bank transfer
            response = self._process_bank_transfer(bank, transfer_data, idempotency_key)
            
            if "error" in response:
                logger.warning(f"Error in transfer: {response['error']}")
                return self._response(
                    self._generate_template(error_message=response['error']),
                    status.HTTP_400_BAD_REQUEST
                )
            
            # Save the transfer
            transfer = serializer.save(
                idempotency_key=idempotency_key,
                status="ACCP"
            )
            
            try:
                # Generate SEPA XML
                sepa_xml = generate_sepa_xml(transfer)
                
                # Return success response
                return self._response(
                    self._generate_template(transfer, sepa_xml),
                    status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                return self._response(
                    self._generate_template(error_message="Error generating SEPA XML"),
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except APIException as e:
            logger.error(f"Error in transfer: {str(e)}")
            return self._response({"error": str(e)}, status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException("Unexpected error in bank transfer.")
    
    def _process_bank_transfer(self, bank: str, transfer_data: Dict[str, Any], 
                              idempotency_key: str) -> Dict[str, Any]:
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
            return transfer_functions[bank](
                transfer_data.get("source_account", ""),
                transfer_data.get("destination_account", ""),
                transfer_data.get("amount"),
                transfer_data.get("currency"),
                idempotency_key
            )
            
        except Exception as e:
            logger.error(f"Error processing bank transfer: {str(e)}", exc_info=True)
            raise APIException("Error processing bank transfer.")


class SEPAViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SEPA transfers.
    
    Provides CRUD operations for SEPA transfers via API.
    """
    queryset = SEPA.objects.all().order_by('-request_date')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Returns:
            Type[serializers.Serializer]: The appropriate serializer class
        """
        if self.action == 'list':
            return SEPAListSerializer
        return SEPASerializer
    
    def perform_create(self, serializer):
        """
        Create a new SEPA transfer.
        
        Args:
            serializer: The validated serializer
        """
        # Generate a unique idempotency key if not provided
        idempotency_key = self.request.headers.get("Idempotency-Key", None)
        
        if not idempotency_key:
            import uuid
            idempotency_key = str(uuid.uuid4())
        
        serializer.save(idempotency_key=idempotency_key, status="PDNG")
    
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
            return Response({"sepa_xml": sepa_xml})
            
        except Exception as e:
            logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            return Response(
                {"error": "Error generating SEPA XML"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Web Interface Views
class TransferListView(ListView):
    """
    View for listing SEPA transfers in the web interface.
    """
    model = SEPA
    template_name = "api/transactions/sepa_list.html"
    context_object_name = "transfers"
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get SEPA transfers with optional filtering.
        
        Returns:
            QuerySet: Filtered SEPA transfers
        """
        queryset = SEPA.objects.all().order_by('-request_date')
        
        # Apply filters if provided
        status_filter = self.request.GET.get('status')
        beneficiary = self.request.GET.get('beneficiary')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if beneficiary:
            queryset = queryset.filter(beneficiary_name__name__icontains=beneficiary)
        if date_from:
            queryset = queryset.filter(request_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(request_date__lte=date_to)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA Transfers')
        
        # Add filter values to context
        context['filters'] = {
            'status': self.request.GET.get('status', ''),
            'beneficiary': self.request.GET.get('beneficiary', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', '')
        }
        
        return context


class TransferCreateView(CreateView):
    """
    View for creating a new SEPA transfer in the web interface.
    """
    model = SEPA
    form_class = SEPAForm
    template_name = "api/transactions/sepa_form.html"
    
    def get_success_url(self):
        """
        Get the URL to redirect to after successful form submission.
        
        Returns:
            str: Success URL
        """
        return reverse_lazy('sepa_list')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create SEPA Transfer')
        context['beneficiaries'] = Debtor.objects.all()
        return context
    
    def form_valid(self, form):
        """
        Process a valid form submission.
        
        Args:
            form: The validated form
            
        Returns:
            HttpResponse: Redirect response
        """
        # Generate a unique idempotency key
        import uuid
        idempotency_key = str(uuid.uuid4())
        
        # Set default values
        form.instance.idempotency_key = idempotency_key
        form.instance.status = "PDNG"
        
        # Save the form
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, _('SEPA transfer created successfully'))
        
        # Generate SEPA XML
        try:
            generate_sepa_xml(self.object)
        except Exception as e:
            logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            messages.warning(self.request, _('Transfer created but XML generation failed'))
        
        return response


class TransferUpdateView(UpdateView):
    """
    View for updating a SEPA transfer in the web interface.
    """
    model = SEPA
    form_class = SEPAForm
    template_name = "api/transactions/sepa_form.html"
    
    def get_success_url(self):
        """
        Get the URL to redirect to after successful form submission.
        
        Returns:
            str: Success URL
        """
        return reverse_lazy('sepa_list')
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update SEPA Transfer')
        context['beneficiaries'] = Debtor.objects.all()
        return context
    
    def form_valid(self, form):
        """
        Process a valid form submission.
        
        Args:
            form: The validated form
            
        Returns:
            HttpResponse: Redirect response
        """
        response = super().form_valid(form)
        messages.success(self.request, _('SEPA transfer updated successfully'))
        return response


class TransferDeleteView(DeleteView):
    """
    View for deleting a SEPA transfer in the web interface.
    """
    model = SEPA
    template_name = "api/transactions/sepa_confirm_delete.html"
    
    def get_success_url(self):
        """
        Get the URL to redirect to after successful deletion.
        
        Returns:
            str: Success URL
        """
        return reverse_lazy("sepa_list")
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete SEPA Transfer')
        return context
    
    def delete(self, request, *args, **kwargs):
        """
        Delete the SEPA transfer and show a success message.
        
        Returns:
            HttpResponse: Redirect response
        """
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _('SEPA transfer deleted successfully'))
        return response


class TransferDetailView(DetailView):
    """
    View for displaying details of a SEPA transfer in the web interface.
    """
    model = SEPA
    template_name = "api/transactions/sepa_detail.html"
    context_object_name = "transfer"
    
    def get_context_data(self, **kwargs):
        """
        Add additional context data.
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA Transfer Details')
        
        # Add attachments to context
        context['attachments'] = self.object.attachments.all()
        
        try:
            # Add generated XML to context
            context['sepa_xml'] = generate_sepa_xml(self.object)
        except Exception as e:
            logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            context['xml_error'] = _('Error generating SEPA XML')
        
        return context
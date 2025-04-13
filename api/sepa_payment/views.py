"""
Views for the SEPA Payment application.

This module defines view functions and classes for handling SEPA payment
operations, including both web interface views and API endpoints.
"""
import json
import logging
from typing import Any, Dict, Optional, Union

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.sepa_payment.forms import SepaCreditTransferForm
from api.sepa_payment.models import SepaCreditTransfer, SepaCreditTransferStatus
from api.sepa_payment.serializers import (
    SepaCreditTransferSerializer, 
    SepaCreditTransferStatusSerializer
)
from api.sepa_payment.services import SepaPaymentService


# Configure logger
logger = logging.getLogger(__name__)


# Web Interface Views
def index(request: HttpRequest) -> HttpResponse:
    """
    Display the SEPA payment application home page.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered home page template
    """
    return render(request, 'partials/navGeneral/sepa_payment/index.html')


@require_http_methods(['GET', 'POST'])
def create_transfer(request: HttpRequest) -> HttpResponse:
    """
    Handle the creation of a new SEPA credit transfer.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered form or redirect
    """
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                # Create the transfer using the service
                service = SepaPaymentService()
                payment_id = service.create_payment(form.cleaned_data)
                
                # Save to database
                transfer = form.save(commit=False)
                transfer.payment_id = payment_id
                transfer.transaction_status = 'PDNG'  # Set initial status
                transfer.save()
                
                messages.success(request, _('Transfer created successfully'))
                return redirect('sepa_payment:list_transfers')
                
            except Exception as e:
                logger.error(f"Error creating transfer: {str(e)}", exc_info=True)
                messages.error(request, _('Error creating transfer: {0}').format(str(e)))
                return render(request, 'api/sepa_payment/transfer.html', {'form': form})
    else:
        form = SepaCreditTransferForm()
    
    return render(request, 'api/sepa_payment/transfer.html', {
        'form': form,
        'title': _('Create SEPA Credit Transfer')
    })


def list_transfers(request: HttpRequest) -> HttpResponse:
    """
    Display a paginated list of SEPA credit transfers.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered list template
    """
    # Get all transfers ordered by creation date
    transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        transfers = transfers.filter(transaction_status=status_filter)
    if date_from:
        transfers = transfers.filter(created_at__gte=date_from)
    if date_to:
        transfers = transfers.filter(created_at__lte=date_to)
    
    # Set up pagination
    paginator = Paginator(transfers, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'api/sepa_payment/list_transfers.html', {
        'page_obj': page_obj,
        'title': _('SEPA Credit Transfers'),
        'filters': {
            'status': status_filter,
            'date_from': date_from,
            'date_to': date_to
        }
    })


def transfer_status(request: HttpRequest, payment_id: str) -> HttpResponse:
    """
    Display the status and history of a SEPA credit transfer.
    
    Args:
        request: The HTTP request
        payment_id: The ID of the payment to display
        
    Returns:
        HttpResponse: Rendered status template or redirect
    """
    try:
        # Get the transfer with the provided ID
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
        
        # Get status history, ordered by timestamp (newest first)
        status_history = transfer.status_history.all().order_by('-timestamp')
        
        # Get latest status
        latest_status = status_history.first() if status_history.exists() else None
        
        # Try to get updated status from the API
        service = SepaPaymentService()
        try:
            api_status = service.get_payment_status(payment_id)
            
            # If API status is different from our latest status, update it
            if latest_status and api_status.get('transactionStatus') != latest_status.status:
                service.update_payment_status(payment_id, api_status.get('transactionStatus'))
                
                # Refresh data
                status_history = transfer.status_history.all().order_by('-timestamp')
                latest_status = status_history.first()
                
        except Exception as e:
            logger.warning(f"Could not retrieve latest status from API: {str(e)}")
            messages.warning(request, _('Using locally stored status, could not connect to payment provider'))
        
        return render(request, 'api/sepa_payment/status.html', {
            'transfer': transfer,
            'latest_status': latest_status,
            'status_history': status_history,
            'errors': transfer.errors.all(),
            'title': _('Transfer Status')
        })
        
    except Exception as e:
        logger.error(f"Error retrieving transfer status: {str(e)}", exc_info=True)
        messages.error(request, _('Error retrieving transfer status'))
        return redirect('sepa_payment:index_sepa_payment')


# API Views
class TransferListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating SEPA credit transfers.
    
    GET: List all transfers
    POST: Create a new transfer
    """
    serializer_class = SepaCreditTransferSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return transfers ordered by creation date."""
        queryset = SepaCreditTransfer.objects.all().order_by('-created_at')
        
        # Apply filters if provided
        status = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if status:
            queryset = queryset.filter(transaction_status=status)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset
    
    def perform_create(self, serializer):
        """Create a new transfer using the payment service."""
        try:
            # Prepare data for the payment service
            data = serializer.validated_data
            
            # Create the payment via the service
            service = SepaPaymentService()
            payment_id = service.create_payment(data)
            
            # Save with the payment ID from the service
            serializer.save(payment_id=payment_id, transaction_status='PDNG')
            
            logger.info(f"API created transfer with payment_id {payment_id}")
            
        except Exception as e:
            logger.error(f"API error creating transfer: {str(e)}", exc_info=True)
            raise


class TransferRetrieveAPIView(generics.RetrieveAPIView):
    """
    API view for retrieving a specific SEPA credit transfer.
    
    GET: Retrieve a transfer
    """
    queryset = SepaCreditTransfer.objects.all()
    serializer_class = SepaCreditTransferSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'payment_id'


class TransferStatusAPIView(APIView):
    """
    API view for retrieving and updating the status of a SEPA credit transfer.
    
    GET: Retrieve transfer status
    POST: Update transfer status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        """Get the current status of a transfer."""
        try:
            # Get the transfer
            transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
            
            # Get status history
            status_history = transfer.status_history.all().order_by('-timestamp')
            latest_status = status_history.first() if status_history.exists() else None
            
            # Try to get updated status from API
            service = SepaPaymentService()
            try:
                api_status = service.get_payment_status(payment_id)
                
                # If API status is different from our latest status, update it
                if latest_status and api_status.get('transactionStatus') != latest_status.status:
                    service.update_payment_status(payment_id, api_status.get('transactionStatus'))
                    
                    # Refresh data
                    status_history = transfer.status_history.all().order_by('-timestamp')
                    latest_status = status_history.first()
                    
            except Exception as e:
                logger.warning(f"API couldn't retrieve latest status: {str(e)}")
            
            # Prepare response data
            response_data = {
                'payment_id': payment_id,
                'current_status': latest_status.status if latest_status else 'UNKNOWN',
                'status_history': SepaCreditTransferStatusSerializer(status_history, many=True).data
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"API error retrieving status: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, payment_id):
        """Update the status of a transfer."""
        try:
            # Validate input
            new_status = request.data.get('status')
            if not new_status:
                return Response(
                    {'error': 'Status is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            service = SepaPaymentService()
            success = service.update_payment_status(payment_id, new_status)
            
            if success:
                return Response({'message': 'Status updated successfully'})
            else:
                return Response(
                    {'error': 'Failed to update status'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"API error updating status: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
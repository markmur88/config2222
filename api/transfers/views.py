"""
Views for the Transfers application.

This module defines views for managing transfers, including both API endpoints
and web interface views for various transfer types.
"""
import logging
import os
import uuid
from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from api.core.services import generate_sepa_xml
from api.transfers.forms import SEPA2Form
from api.transfers.models import SEPA2, SEPA3, SepaTransaction, Transfer
from api.transfers.serializers import (
    SEPA2Serializer, 
    SEPA2ListSerializer,
    TransferSerializer,
    SepaTransactionSerializer
)


# Configure logger
logger = logging.getLogger("bank_services")


# API Views for standard transfers
class TransferVIEWList(generics.ListCreateAPIView):
    """API view for listing and creating transfers."""
    queryset = SEPA2.objects.all().order_by('-request_date')
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return list serializer for GET requests."""
        if self.request.method == 'GET':
            return SEPA2ListSerializer
        return SEPA2Serializer
    
    def get_queryset(self):
        """Filter transfers based on query parameters."""
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status')
        account = self.request.query_params.get('account')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if account:
            queryset = queryset.filter(account_name__icontains=account)
            
        return queryset


class TransferVIEWDetail(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating, and deleting a transfer."""
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]


class TransferVIEWCreateView(APIView):
    """API view for creating transfers."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a transfer",
        request_body=SEPA2Serializer
    )
    def post(self, request):
        """Create a new transfer."""
        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"error": _("Idempotency-Key header is required")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicate transfer
        existing_transfer = SEPA2.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transfer:
            return Response(
                {
                    "message": _("Duplicate transfer"), 
                    "transfer_id": str(existing_transfer.id)
                },
                status=status.HTTP_200_OK
            )
        
        # Validate request data
        serializer = SEPA2Serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        transfer_data = serializer.validated_data
        bank = request.data.get("bank")
        
        try:
            # Process with appropriate bank service
            if bank == "memo":
                response = memo_bank_transfer(
                    transfer_data.get("source_account", ""),
                    transfer_data.get("destination_account", ""),
                    transfer_data.get("amount"),
                    transfer_data.get("currency"),
                    idempotency_key
                )
            elif bank == "deutsche":
                response = deutsche_bank_transfer(
                    transfer_data.get("source_account", ""),
                    transfer_data.get("destination_account", ""),
                    transfer_data.get("amount"),
                    transfer_data.get("currency"),
                    idempotency_key
                )
            else:
                return Response(
                    {"error": _("Invalid bank selection")}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for errors in bank response
            if "error" in response:
                logger.warning(f"Error in transfer: {response['error']}")
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
            # Save the transfer
            transfer = serializer.save(
                idempotency_key=idempotency_key, 
                status="ACCP",
                created_by=request.user
            )
            
            # Try to generate SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transfer)
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                
                # Add XML to response
                response_data = serializer.data
                response_data['sepa_xml'] = sepa_xml
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                # Continue without XML
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.critical(f"Critical error in transfer: {str(e)}", exc_info=True)
            raise APIException(_("Unexpected error in bank transfer."))
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Template Views for standard transfers
def transferVIEW_create_view(request):
    """View for creating a new transfer with a form."""
    if request.method == 'POST':
        form = SEPA2Form(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.created_by = request.user
            transfer.save()
            
            messages.success(request, _("Transfer created successfully"))
            
            # Try to generate SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transfer)
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
        try:
            form = SEPA2Form()
        except Exception as e:
            messages.error(request, _(f"Error loading form: {str(e)}"))
            form = None
    
    return render(request, 'api/transfers/transfer_form.html', {
        'form': form,
        'title': _('Create Transfer')
    })


def transferVIEW_update_view(request, pk):
    """View for updating an existing transfer."""
    transfer = get_object_or_404(SEPA2, pk=pk)
    
    if request.method == 'POST':
        form = SEPA2Form(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            messages.success(request, _("Transfer updated successfully"))
            return HttpResponseRedirect(reverse('transfer_detail', args=[pk]))
        else:
            messages.error(request, _("Please correct the errors below"))
    else:
        form = SEPA2Form(instance=transfer)
    
    return render(request, 'api/transfers/transfer_form.html', {
        'form': form,
        'transfer': transfer,
        'title': _('Update Transfer')
    })


# API Views for SEPA transfers
class SepaTransferVIEWCreateView(APIView):
    """API view for creating SEPA transfers."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a SEPA transfer",
        request_body=SEPA2Serializer
    )
    def post(self, request):
        """Create a new SEPA transfer."""
        # Use the standard header name for consistency
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"error": _("Idempotency-Key header is required")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicate using transaction_id
        existing_transaction = SEPA2.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            return Response(
                {
                    "message": _("Duplicate SEPA transfer"),
                    "transaction_id": str(existing_transaction.id)
                }, 
                status=status.HTTP_200_OK
            )
        
        # Validate request data
        serializer = SEPA2Serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the transaction and create XML
        transaction = serializer.save(
            idempotency_key=idempotency_key,
            created_by=request.user
        )
        
        try:
            sepa_xml = generate_sepa_xml(transaction)
            media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transaction.id}.xml")
            with open(media_path, "w") as xml_file:
                xml_file.write(sepa_xml)
                
            return Response(
                {"sepa_xml": sepa_xml, "transaction": serializer.data},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.critical(f"Error generating SEPA XML: {str(e)}", exc_info=True)
            raise APIException(_("Unexpected error during SEPA transfer."))


class SepaTransferVIEWListView(generics.ListAPIView):
    """API view for listing SEPA transfers."""
    queryset = SEPA2.objects.all().order_by('-request_date')
    serializer_class = SEPA2ListSerializer
    permission_classes = [IsAuthenticated]


class SepaTransferVIEWUpdateView(generics.UpdateAPIView):
    """API view for updating a SEPA transfer."""
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]


class SepaTransferVIEWDeleteView(generics.DestroyAPIView):
    """API view for deleting a SEPA transfer."""
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]


# Template Views for SEPA transactions
def sepa_transactionVIEW_create_view(request):
    """View for creating a new SEPA transaction with a form."""
    if request.method == 'POST':
        form = SEPA2Form(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            
            messages.success(request, _("SEPA transaction created successfully"))
            
            # Try to generate SEPA XML
            try:
                sepa_xml = generate_sepa_xml(transaction)
                media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transaction.id}.xml")
                with open(media_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
                messages.info(request, _("SEPA XML generated successfully"))
            except Exception as e:
                logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                messages.warning(request, _("Transaction created but XML generation failed"))
                
            return HttpResponseRedirect(reverse('sepa_transfer_list'))
        else:
            messages.error(request, _("Please correct the errors below"))
    else:
        form = SEPA2Form()
    
    return render(request, 'api/transfers/sepa_transaction_form.html', {
        'form': form,
        'title': _('Create SEPA Transaction')
    })


def sepa_transactionVIEW_update_view(request, pk):
    """View for updating an existing SEPA transaction."""
    transaction = get_object_or_404(SEPA2, pk=pk)
    
    if request.method == 'POST':
        form = SEPA2Form(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, _("SEPA transaction updated successfully"))
            return HttpResponseRedirect(reverse('sepa-transaction-detail', args=[pk]))
        else:
            messages.error(request, _("Please correct the errors below"))
    else:
        form = SEPA2Form(instance=transaction)
    
    return render(request, 'api/transfers/sepa_transaction_form.html', {
        'form': form,
        'transaction': transaction,
        'title': _('Update SEPA Transaction')
    })


# Additional API views
class SEPA2VIEWList(generics.ListCreateAPIView):
    """API view for listing and creating SEPA2 transfers."""
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]


class SEPA2VIEWDetail(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating, and deleting a SEPA2 transfer."""
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    permission_classes = [IsAuthenticated]


# List views for templates
class TRANSFERLV(ListView):
    """View for listing Transfer objects."""
    model = Transfer
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Transfers')
        return context


class SEPATRANSACTIONLV(ListView):
    """View for listing SepaTransaction objects."""
    model = SepaTransaction
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA Transactions')
        return context


class SEPA2LV(ListView):
    """View for listing SEPA2 objects."""
    model = SEPA2
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA2 Transfers')
        return context


class SEPA3LV(ListView):
    """View for listing SEPA3 objects."""
    model = SEPA3
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('SEPA3 Transfers')
        return context
"""
Views for the Transactions application.

This module defines both API endpoints and web interface views for
managing standard transactions (non-SEPA).
"""
import logging
from typing import Any, Dict, Optional, Union

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.accounts.models import Account
from api.transactions.forms import TransactionForm
from api.transactions.models import Transaction, TransactionAttachment
from api.transactions.serializers import (
    TransactionSerializer, 
    TransactionListSerializer,
    TransactionAttachmentSerializer
)


# Configure logger
logger = logging.getLogger("transactions")


# API Views
class TransactionList(generics.ListCreateAPIView):
    """
    API view for listing and creating transactions.
    
    GET: List all transactions for the authenticated user
    POST: Create a new transaction
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return transactions for the authenticated user with optional filtering.
        
        Returns:
            QuerySet: Filtered Transaction queryset
        """
        user = self.request.user
        queryset = Transaction.objects.filter(created_by=user).order_by('-request_date')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        direction = self.request.query_params.get('direction')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(request_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(request_date__lte=date_to)
        if direction:
            queryset = queryset.filter(direction=direction)
            
        return queryset
    
    def get_serializer_class(self):
        """
        Return different serializers based on the request method.
        
        Returns:
            Type[serializers.Serializer]: The appropriate serializer
        """
        if self.request.method == 'GET':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """
        Create a new transaction with the authenticated user as owner.
        
        Args:
            serializer: The serializer instance with validated data
        """
        # Get idempotency key from header
        idempotency_key = self.request.headers.get("Idempotency-Key")
        
        if not idempotency_key:
            # Generate a unique idempotency key if not provided
            import uuid
            idempotency_key = str(uuid.uuid4())
        
        # Save with the authenticated user as owner
        serializer.save(
            created_by=self.request.user,
            idempotency_key=idempotency_key,
            status="PDNG"
        )


class TransactionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a transaction.
    
    GET: Retrieve a transaction
    PUT/PATCH: Update a transaction
    DELETE: Delete a transaction
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Return transactions for the authenticated user.
        
        Returns:
            QuerySet: Transaction queryset filtered by user
        """
        user = self.request.user
        return Transaction.objects.filter(created_by=user)
    
    def perform_update(self, serializer):
        """
        Update a transaction and log the change.
        
        Args:
            serializer: The serializer instance with validated data
        """
        transaction = serializer.save()
        logger.info(f"Transaction updated: {transaction.id} by {self.request.user}")


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Transaction model.
    
    Provides CRUD operations for Transaction objects.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """
        Return transactions for the authenticated user with optional filtering.
        
        Returns:
            QuerySet: Filtered Transaction queryset
        """
        user = self.request.user
        queryset = Transaction.objects.filter(created_by=user).order_by('-request_date')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        direction = self.request.query_params.get('direction')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(request_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(request_date__lte=date_to)
        if direction:
            queryset = queryset.filter(direction=direction)
            
        return queryset
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Returns:
            Type[serializers.Serializer]: The appropriate serializer
        """
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """
        Create a new transaction with the authenticated user as owner.
        
        Args:
            serializer: The serializer instance with validated data
        """
        # Get idempotency key from header
        idempotency_key = self.request.headers.get("Idempotency-Key")
        
        if not idempotency_key:
            # Generate a unique idempotency key if not provided
            import uuid
            idempotency_key = str(uuid.uuid4())
        
        # Save with the authenticated user as owner
        serializer.save(
            created_by=self.request.user,
            idempotency_key=idempotency_key,
            status="PDNG"
        )
    
    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """
        List attachments for a transaction.
        
        Args:
            request: The HTTP request
            pk: The primary key of the transaction
            
        Returns:
            Response: List of attachments
        """
        transaction = self.get_object()
        attachments = transaction.attachments.all()
        serializer = TransactionAttachmentSerializer(
            attachments, 
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        """
        Add an attachment to a transaction.
        
        Args:
            request: The HTTP request
            pk: The primary key of the transaction
            
        Returns:
            Response: Created attachment or error
        """
        transaction = self.get_object()
        
        # Check if file was uploaded
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file was uploaded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        
        # Create attachment
        attachment = TransactionAttachment.objects.create(
            transaction=transaction,
            file=file_obj,
            filename=file_obj.name,
            file_type=file_obj.content_type,
            file_size=file_obj.size,
            description=request.data.get('description', '')
        )
        
        # Update attachment count
        transaction.attachment_count = transaction.attachments.count()
        transaction.save(update_fields=['attachment_count'])
        
        # Return attachment data
        serializer = TransactionAttachmentSerializer(
            attachment,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Web Interface Views
def transaction_list(request: HttpRequest) -> HttpResponse:
    """
    Display a paginated list of transactions.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered transaction list
    """
    # Get transactions for the user
    user = request.user
    transactions = Transaction.objects.filter(created_by=user).order_by('-request_date')
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    direction = request.GET.get('direction')
    
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    if date_from:
        transactions = transactions.filter(request_date__gte=date_from)
    if date_to:
        transactions = transactions.filter(request_date__lte=date_to)
    if direction:
        transactions = transactions.filter(direction=direction)
    
    # Set up pagination
    paginator = Paginator(transactions, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare context
    context = {
        'page_obj': page_obj,
        'title': _('Transactions'),
        'filters': {
            'status': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'direction': direction
        }
    }
    
    return render(request, 'api/transactions/transaction_list.html', context)


def transaction_create(request: HttpRequest) -> HttpResponse:
    """
    Create a new transaction.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered form or redirect
    """
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            # Create but don't save yet
            transaction = form.save(commit=False)
            
            # Set user and generate idempotency key
            transaction.created_by = request.user
            
            import uuid
            transaction.idempotency_key = uuid.uuid4()
            
            # Set initial status
            transaction.status = "PDNG"
            
            # Save the transaction
            transaction.save()
            
            # Add success message
            messages.success(request, _('Transaction created successfully'))
            
            # Redirect to transaction list
            return redirect('transaction_list')
        else:
            # If form is invalid, show errors
            messages.error(request, _('Please correct the errors below'))
    else:
        # Create a new form
        form = TransactionForm()
    
    # Render the form
    context = {
        'form': form,
        'title': _('Create Transaction')
    }
    return render(request, 'api/transactions/transaction_form.html', context)


def transaction_detail(request: HttpRequest, pk: str) -> HttpResponse:
    """
    Display details of a transaction.
    
    Args:
        request: The HTTP request
        pk: The primary key of the transaction
        
    Returns:
        HttpResponse: Rendered transaction detail
    """
    # Get the transaction
    transaction = get_object_or_404(Transaction, pk=pk, created_by=request.user)
    
    # Get attachments
    attachments = transaction.attachments.all()
    
    # Prepare context
    context = {
        'transaction': transaction,
        'attachments': attachments,
        'title': _('Transaction Details')
    }
    
    return render(request, 'api/transactions/transaction_detail.html', context)


def transaction_update(request: HttpRequest, pk: str) -> HttpResponse:
    """
    Update an existing transaction.
    
    Args:
        request: The HTTP request
        pk: The primary key of the transaction
        
    Returns:
        HttpResponse: Rendered form or redirect
    """
    # Get the transaction
    transaction = get_object_or_404(Transaction, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # Save the updated transaction
            form.save()
            
            # Add success message
            messages.success(request, _('Transaction updated successfully'))
            
            # Redirect to transaction list
            return redirect('transaction_list')
        else:
            # If form is invalid, show errors
            messages.error(request, _('Please correct the errors below'))
    else:
        # Create form with existing data
        form = TransactionForm(instance=transaction)
    
    # Render the form
    context = {
        'form': form,
        'transaction': transaction,
        'title': _('Update Transaction')
    }
    return render(request, 'api/transactions/transaction_form.html', context)


def transaction_delete(request: HttpRequest, pk: str) -> HttpResponse:
    """
    Delete a transaction.
    
    Args:
        request: The HTTP request
        pk: The primary key of the transaction
        
    Returns:
        HttpResponse: Rendered confirmation or redirect
    """
    # Get the transaction
    transaction = get_object_or_404(Transaction, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        # Delete the transaction
        transaction.delete()
        
        # Add success message
        messages.success(request, _('Transaction deleted successfully'))
        
        # Redirect to transaction list
        return redirect('transaction_list')
    
    # Render confirmation page
    context = {
        'transaction': transaction,
        'title': _('Delete Transaction')
    }
    return render(request, 'api/transactions/transaction_confirm_delete.html', context)
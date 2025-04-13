"""
Views for the Sandbox application.

This module defines both API views and web interface views for the sandbox functionality,
providing simulated banking operations for testing and development.
"""
import logging
from typing import Any, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.auth_services import get_deutsche_bank_token, get_memo_bank_token
from api.core.utils import deutsche_bank_request, memo_bank_request, get_deutsche_bank_accounts, get_memo_bank_accounts
from api.sandbox.forms import IncomingCollectionForm, IncomingCollectionSearchForm, SandboxSettingsForm
from api.sandbox.models import IncomingCollection, SandboxBankAccount, SandboxTransaction
from api.sandbox.serializers import (
    IncomingCollectionSerializer, IncomingCollectionApproveSerializer,
    SandboxBankAccountSerializer, SandboxTransactionSerializer
)
from api.sandbox.services import (
    process_incoming_collection, get_account_balance, initiate_sepa_transfer,
    approve_collection, get_transaction_status
)


# Configure logger
logger = logging.getLogger(__name__)


# API Views
class BankConnectionTest(APIView):
    """
    API view for testing bank connections.
    
    GET: Test connectivity to supported banks
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Test bank connections",
        responses={200: "Connection test results"}
    )
    def get(self, request: Request) -> Response:
        """
        Test connections to various banking APIs.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Connection test results
        """
        # Test Memo Bank
        memo_response = memo_bank_request("test-connection", {})
        
        # Test Deutsche Bank
        db_response = deutsche_bank_request("test-connection", {})
        
        logger.info("Bank connection test performed")
        return Response({
            "memo_bank": memo_response,
            "deutsche_bank": db_response
        })


class BankAuthView(APIView):
    """
    API view for testing bank authentication.
    
    GET: Get authentication tokens from supported banks
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get bank authentication tokens",
        responses={200: "Authentication tokens"}
    )
    def get(self, request: Request) -> Response:
        """
        Get authentication tokens from supported banks.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Authentication tokens
        """
        memo_token = get_memo_bank_token().get("access_token")
        deutsche_token = get_deutsche_bank_token().get("access_token")
        
        logger.info("Bank authentication tokens retrieved")
        return Response({
            "memo_bank_token": memo_token,
            "deutsche_bank_token": deutsche_token
        })


class BankAccountsView(APIView):
    """
    API view for retrieving bank accounts.
    
    GET: List accounts from supported banks
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get bank accounts",
        responses={200: "Bank accounts"}
    )
    def get(self, request: Request) -> Response:
        """
        Get accounts from supported banks.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Bank accounts
        """
        try:
            # Get Deutsche Bank accounts
            deutsche_token = get_deutsche_bank_token().get("access_token")
            deutsche_accounts = get_deutsche_bank_accounts(deutsche_token) if deutsche_token else {"error": "No token"}
            
            # Get Memo Bank accounts
            memo_token = get_memo_bank_token().get("access_token")
            memo_accounts = get_memo_bank_accounts(memo_token) if memo_token else {"error": "No token"}
            
            logger.info("Bank accounts retrieved")
            return Response({
                "deutsche_bank_accounts": deutsche_accounts,
                "memo_bank_accounts": memo_accounts
            })
        except Exception as e:
            logger.error(f"Error retrieving bank accounts: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error retrieving bank accounts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncomingCollectionAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating incoming collections.
    
    GET: List all incoming collections
    POST: Create a new incoming collection
    """
    queryset = IncomingCollection.objects.all()
    serializer_class = IncomingCollectionSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference_id', 'sender_name', 'sender_iban', 'recipient_iban']
    ordering_fields = ['transaction_date', 'amount', 'status']
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on query parameters.
        
        Returns:
            QuerySet: Filtered queryset of incoming collections
        """
        queryset = IncomingCollection.objects.all()
        
        # Apply filters if provided
        status = self.request.query_params.get('status')
        reference_id = self.request.query_params.get('reference_id')
        sender_name = self.request.query_params.get('sender_name')
        
        if status:
            queryset = queryset.filter(status=status)
        if reference_id:
            queryset = queryset.filter(reference_id__icontains=reference_id)
        if sender_name:
            queryset = queryset.filter(sender_name__icontains=sender_name)
            
        return queryset
    
    @swagger_auto_schema(
        operation_description="List incoming collections",
        responses={200: IncomingCollectionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """List all incoming collections with optional filtering."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create an incoming collection",
        request_body=IncomingCollectionSerializer,
        responses={201: IncomingCollectionSerializer()}
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Process an incoming collection in the sandbox.
        
        Args:
            request: The HTTP request with collection data
            
        Returns:
            Response: Created collection or validation errors
        """
        serializer = IncomingCollectionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                collection = process_incoming_collection(serializer.validated_data)
                logger.info(f"Incoming collection processed: {collection.reference_id}")
                return Response(
                    IncomingCollectionSerializer(collection).data, 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Error processing incoming collection: {str(e)}", exc_info=True)
                return Response(
                    {"error": f"Error processing collection: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncomingCollectionDetailAPIView(viewsets.ModelViewSet):
    """
    API view for retrieving, updating, or deleting an incoming collection.
    
    GET: Retrieve an incoming collection
    PUT: Update an incoming collection
    DELETE: Delete an incoming collection
    """
    queryset = IncomingCollection.objects.all()
    serializer_class = IncomingCollectionSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    
    @swagger_auto_schema(
        operation_description="Retrieve an incoming collection",
        responses={200: IncomingCollectionSerializer()}
    )
    def retrieve(self, request, *args, **kwargs) -> Response:
        """Retrieve a specific incoming collection."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update an incoming collection",
        request_body=IncomingCollectionSerializer,
        responses={200: IncomingCollectionSerializer()}
    )
    def update(self, request, *args, **kwargs) -> Response:
        """Update an incoming collection."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete an incoming collection",
        responses={204: "No content"}
    )
    def destroy(self, request, *args, **kwargs) -> Response:
        """Delete an incoming collection."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Approve or reject an incoming collection",
        request_body=IncomingCollectionApproveSerializer,
        responses={200: "Approval result"}
    )
    def approve(self, request, pk=None) -> Response:
        """
        Approve or reject an incoming collection.
        
        Args:
            request: The HTTP request with approval data
            pk: The primary key of the collection
            
        Returns:
            Response: Result of the approval/rejection
        """
        serializer = IncomingCollectionApproveSerializer(data=request.data)
        if serializer.is_valid():
            approve_decision = serializer.validated_data['approve']
            reason = serializer.validated_data.get('reason')
            
            result = approve_collection(pk, approve_decision, reason)
            if result.get('success'):
                return Response(result, status=status.HTTP_200_OK)
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountBalanceView(APIView):
    """
    API view for retrieving account balances.
    
    GET: Get balance for a specific account
    """
    permission_classes = [AllowAny]  # Sandbox is open for testing
    
    @swagger_auto_schema(
        operation_description="Get account balance",
        responses={200: "Account balance details"}
    )
    def get(self, request: Request, account_id: str) -> Response:
        """
        Get balance for a simulated account.
        
        Args:
            request: The HTTP request
            account_id: The ID of the account
            
        Returns:
            Response: Account balance information
        """
        try:
            balance = get_account_balance(account_id)
            logger.info(f"Retrieved balance for account {account_id}")
            return Response(balance, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving account balance: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error retrieving balance: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SepaTransferView(viewsets.ViewSet):
    """
    API view for simulating SEPA transfers.
    
    POST: Initiate a SEPA transfer
    GET: Get status of a SEPA transfer
    """
    permission_classes = [AllowAny]  # Sandbox is open for testing
    
    @swagger_auto_schema(
        operation_description="Initiate a SEPA transfer",
        responses={201: "Transfer result", 400: "Bad request"}
    )
    def create(self, request: Request) -> Response:
        """
        Initiate a simulated SEPA transfer.
        
        Args:
            request: The HTTP request with transfer data
            
        Returns:
            Response: Transfer result
        """
        try:
            response = initiate_sepa_transfer(request.data)
            
            if "error" in response:
                logger.warning(f"SEPA transfer failed: {response['error']}")
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
                
            logger.info(f"SEPA transfer initiated: {response.get('transaction_id')}")
            return Response(response, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error initiating SEPA transfer: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error initiating transfer: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Check status of a SEPA transfer",
        responses={200: "Transfer status"}
    )
    @action(detail=True, methods=['get'])
    def status(self, request: Request, transaction_id: str) -> Response:
        """
        Get the status of a SEPA transfer.
        
        Args:
            request: The HTTP request
            transaction_id: The ID of the transaction
            
        Returns:
            Response: Transfer status information
        """
        try:
            status_info = get_transaction_status(transaction_id)
            
            if "error" in status_info:
                logger.warning(f"Error getting transaction status: {status_info['error']}")
                return Response(status_info, status=status.HTTP_404_NOT_FOUND)
                
            logger.info(f"Retrieved status for transaction {transaction_id}")
            return Response(status_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Error checking transaction status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SandboxBankAccountAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating sandbox bank accounts.
    
    GET: List all sandbox bank accounts
    POST: Create a new sandbox bank account
    """
    queryset = SandboxBankAccount.objects.all()
    serializer_class = SandboxBankAccountSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['account_number', 'account_holder']
    ordering_fields = ['account_holder', 'balance']


class SandboxBankAccountDetailAPIView(viewsets.ModelViewSet):
    """
    API view for retrieving, updating, or deleting a sandbox bank account.
    
    GET: Retrieve a sandbox bank account
    PUT: Update a sandbox bank account
    DELETE: Delete a sandbox bank account
    """
    queryset = SandboxBankAccount.objects.all()
    serializer_class = SandboxBankAccountSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None) -> Response:
        """
        Get transactions for a specific account.
        
        Args:
            request: The HTTP request
            pk: The primary key of the account
            
        Returns:
            Response: List of transactions
        """
        account = self.get_object()
        
        # Get both incoming and outgoing transactions
        incoming = account.incoming_transactions.all()
        outgoing = account.outgoing_transactions.all()
        
        # Serialize the transactions
        incoming_data = SandboxTransactionSerializer(incoming, many=True).data
        outgoing_data = SandboxTransactionSerializer(outgoing, many=True).data
        
        return Response({
            "account": SandboxBankAccountSerializer(account).data,
            "incoming_transactions": incoming_data,
            "outgoing_transactions": outgoing_data
        })


class SandboxTransactionAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating sandbox transactions.
    
    GET: List all sandbox transactions
    POST: Create a new sandbox transaction
    """
    queryset = SandboxTransaction.objects.all()
    serializer_class = SandboxTransactionSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transaction_id', 'description']
    ordering_fields = ['-created_at', 'status', 'amount']


class SandboxTransactionDetailAPIView(viewsets.ModelViewSet):
    """
    API view for retrieving, updating, or deleting a sandbox transaction.
    
    GET: Retrieve a sandbox transaction
    PUT: Update a sandbox transaction
    DELETE: Delete a sandbox transaction
    """
    queryset = SandboxTransaction.objects.all()
    serializer_class = SandboxTransactionSerializer
    permission_classes = [AllowAny]  # Sandbox is open for testing
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None) -> Response:
        """
        Process a pending transaction.
        
        Args:
            request: The HTTP request
            pk: The primary key of the transaction
            
        Returns:
            Response: Result of processing
        """
        transaction = self.get_object()
        
        if transaction.status != "PENDING":
            return Response(
                {"error": f"Transaction is not pending (status: {transaction.status})"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = transaction.process()
        
        if success:
            return Response({
                "success": True,
                "transaction": SandboxTransactionSerializer(transaction).data
            })
        else:
            return Response({
                "success": False,
                "error": transaction.error_message,
                "transaction": SandboxTransactionSerializer(transaction).data
            }, status=status.HTTP_400_BAD_REQUEST)


# Web Interface Views
class SandboxDashboardView(TemplateView):
    """
    View for the sandbox dashboard.
    """
    template_name = 'api/sandbox/dashboard.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add dashboard data to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        
        # Get counts for dashboard
        context['total_collections'] = IncomingCollection.objects.count()
        context['pending_collections'] = IncomingCollection.objects.filter(status="PENDING").count()
        context['completed_collections'] = IncomingCollection.objects.filter(status="COMPLETED").count()
        context['total_accounts'] = SandboxBankAccount.objects.count()
        context['total_transactions'] = SandboxTransaction.objects.count()
        
        # Get recent collections and transactions
        context['recent_collections'] = IncomingCollection.objects.all().order_by('-transaction_date')[:5]
        context['recent_transactions'] = SandboxTransaction.objects.all().order_by('-created_at')[:5]
        
        context['title'] = 'Sandbox Dashboard'
        return context


class SandboxSettingsView(UpdateView):
    """
    View for managing sandbox settings.
    """
    template_name = 'api/sandbox/settings.html'
    form_class = SandboxSettingsForm
    success_url = reverse_lazy('sandbox-dashboard')
    
    def get_object(self):
        """Return dummy object for the form."""
        return None
    
    def get_initial(self) -> Dict[str, Any]:
        """
        Get initial form data from settings.
        
        Returns:
            Dict[str, Any]: Initial form data
        """
        from django.conf import settings
        return {
            'auto_approve_collections': getattr(settings, 'SANDBOX_AUTO_APPROVE_COLLECTIONS', False),
            'simulated_delay': getattr(settings, 'SANDBOX_SIMULATED_DELAY', 1),
            'error_rate': getattr(settings, 'SANDBOX_ERROR_RATE', 10),
        }
    
    def form_valid(self, form) -> HttpResponse:
        """
        Save settings and show success message.
        
        Args:
            form: The form with settings data
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        # In a real app, we would save these to the database or settings
        # For this example, we'll just show a success message
        messages.success(self.request, _("Sandbox settings updated successfully"))
        return redirect(self.success_url)


class IncomingCollectionListView(ListView):
    """
    View for displaying a list of incoming collections in the web interface.
    """
    model = IncomingCollection
    template_name = 'api/sandbox/incomingcollection_list.html'
    context_object_name = 'collections'
    paginate_by = 10
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on search form.
        
        Returns:
            QuerySet: Filtered queryset of incoming collections
        """
        queryset = IncomingCollection.objects.all().order_by('-transaction_date')
        
        # Get search form
        form = IncomingCollectionSearchForm(self.request.GET or None)
        
        # Apply filters if form is valid
        if form.is_valid():
            reference_id = form.cleaned_data.get('reference_id')
            sender_name = form.cleaned_data.get('sender_name')
            status = form.cleaned_data.get('status')
            min_amount = form.cleaned_data.get('min_amount')
            max_amount = form.cleaned_data.get('max_amount')
            
            if reference_id:
                queryset = queryset.filter(reference_id__icontains=reference_id)
            if sender_name:
                queryset = queryset.filter(sender_name__icontains=sender_name)
            if status:
                queryset = queryset.filter(status=status)
            if min_amount is not None:
                queryset = queryset.filter(amount__gte=min_amount)
            if max_amount is not None:
                queryset = queryset.filter(amount__lte=max_amount)
                
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add search form and title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = IncomingCollectionSearchForm(self.request.GET or None)
        context['title'] = _("Incoming Collections")
        return context


class IncomingCollectionCreateView(CreateView):
    """
    View for creating a new incoming collection in the web interface.
    """
    model = IncomingCollection
    form_class = IncomingCollectionForm
    template_name = 'api/sandbox/incomingcollection_form.html'
    success_url = reverse_lazy('incoming-collections')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Create Incoming Collection")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission.
        
        Args:
            form: The form with collection data
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        messages.success(self.request, _("Incoming collection created successfully"))
        return response


class IncomingCollectionUpdateView(UpdateView):
    """
    View for updating an existing incoming collection in the web interface.
    """
    model = IncomingCollection
    form_class = IncomingCollectionForm
    template_name = 'api/sandbox/incomingcollection_form.html'
    success_url = reverse_lazy('incoming-collections')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Update Incoming Collection")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission.
        
        Args:
            form: The form with collection data
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        messages.success(self.request, _("Incoming collection updated successfully"))
        return response


class IncomingCollectionDeleteView(DeleteView):
    """
    View for deleting an incoming collection in the web interface.
    """
    model = IncomingCollection
    template_name = 'api/sandbox/incomingcollection_confirm_delete.html'
    success_url = reverse_lazy('incoming-collections')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete Incoming Collection")
        return context
    
    def delete(self, request, *args, **kwargs) -> HttpResponse:
        """
        Handle deletion and show success message.
        
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(self.request, _("Incoming collection deleted successfully"))
        return super().delete(request, *args, **kwargs)
"""
Views for the Accounts application.

This module defines API endpoints and web interface views for account management,
including listing, creating, updating, and deleting accounts.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from typing import Any, Dict, Optional, Union

from api.accounts.forms import AccountForm
from api.accounts.models import Account
from api.accounts.serializers import AccountSerializer, AccountListSerializer, AccountDetailSerializer


# API Views
class AccountListCreate(generics.ListCreateAPIView):
    """
    API view for listing all accounts and creating new ones.
    
    GET: List all accounts
    POST: Create a new account
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        """Return different serializers for list and create actions."""
        if self.request.method == 'GET':
            return AccountListSerializer
        return AccountSerializer
    
    @swagger_auto_schema(
        operation_description="List all accounts or create a new account.",
        responses={200: AccountListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List all accounts."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new account",
        request_body=AccountSerializer,
        responses={201: AccountSerializer()}
    )
    def post(self, request, *args, **kwargs):
        """Create a new account."""
        return super().post(request, *args, **kwargs)


class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting an account.
    
    GET: Retrieve an account
    PUT: Update an account
    PATCH: Partially update an account
    DELETE: Delete an account
    """
    queryset = Account.objects.all()
    serializer_class = AccountDetailSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Retrieve an account",
        responses={200: AccountDetailSerializer()}
    )
    def get(self, request, *args, **kwargs):
        """Retrieve an account."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update an account",
        request_body=AccountSerializer,
        responses={200: AccountDetailSerializer()}
    )
    def put(self, request, *args, **kwargs):
        """Update an account."""
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update an account",
        request_body=AccountSerializer,
        responses={200: AccountDetailSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        """Partially update an account."""
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete an account",
        responses={204: "No content"}
    )
    def delete(self, request, *args, **kwargs):
        """Delete an account."""
        return super().delete(request, *args, **kwargs)


class AccountDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving the authenticated user's account.
    """
    serializer_class = AccountDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return the account belonging to the authenticated user."""
        return self.request.user.account
    
    @swagger_auto_schema(
        operation_description="Retrieve the authenticated user's account",
        responses={200: AccountDetailSerializer()}
    )
    def get(self, request, *args, **kwargs):
        """Retrieve the authenticated user's account."""
        return super().get(request, *args, **kwargs)


# Web Interface Views
class AccountListView(LoginRequiredMixin, ListView):
    """
    View for displaying a list of accounts in the web interface.
    """
    model = Account
    template_name = 'api/accounts/account_list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):
        """Return accounts associated with the current user."""
        return Account.objects.all()
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Accounts'
        return context


class AccountCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new account in the web interface.
    """
    model = Account
    form_class = AccountForm
    template_name = 'api/accounts/account_form.html'
    success_url = reverse_lazy('account_list')
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Account'
        context['action'] = 'Create'
        return context
    
    def form_valid(self, form):
        """Process valid form data and associate the account with the user."""
        # Associate the account with the current user if applicable
        if hasattr(form.instance, 'user') and not form.instance.user:
            form.instance.user = self.request.user
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating an existing account in the web interface.
    """
    model = Account
    form_class = AccountForm
    template_name = 'api/accounts/account_form.html'
    success_url = reverse_lazy('account_list')
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Account'
        context['action'] = 'Update'
        return context
    
    def get_queryset(self):
        """Return accounts associated with the current user."""
        return Account.objects.all()


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting an account in the web interface.
    """
    model = Account
    template_name = 'api/accounts/account_confirm_delete.html'
    success_url = reverse_lazy('account_list')
    
    def get_context_data(self, **kwargs):
        """Add additional context for the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Account'
        return context
    
    def get_queryset(self):
        """Return accounts associated with the current user."""
        return Account.objects.all()
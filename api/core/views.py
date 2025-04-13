"""
Views for the Core application.

This module defines both API views and web interface views for
core functionality, including IBAN and debtor management.
"""
import logging
from typing import Any, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.forms import IBANForm, DebtorForm, IBANSearchForm, DebtorSearchForm
from api.core.models import IBAN, Debtor
from api.core.serializers import (
    IBANSerializer, DebtorSerializer, ErrorResponseSerializer, 
    TransactionStatusSerializer, MessageSerializer
)
from api.core.services import validate_iban, validate_bic


# Configure logger
logger = logging.getLogger(__name__)


# API Views
class CoreHealthCheckView(APIView):
    """
    API view for health checking the Core application.
    
    GET: Returns a status indicating the API is operational
    """
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        """
        Perform a basic health check.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Health status information
        """
        return Response({
            "status": "ok",
            "message": "Core API is operational"
        }, status=status.HTTP_200_OK)


class IBANAPIListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating IBANs.
    
    GET: List all IBANs
    POST: Create a new IBAN
    """
    queryset = IBAN.objects.all()
    serializer_class = IBANSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['iban', 'bic', 'bank_name']
    ordering_fields = ['iban', 'bank_name', 'status']
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on query parameters.
        
        Returns:
            QuerySet: Filtered queryset of IBANs
        """
        queryset = IBAN.objects.all()
        
        # Apply filters if provided
        status = self.request.query_params.get('status')
        type = self.request.query_params.get('type')
        bank_name = self.request.query_params.get('bank_name')
        
        if status:
            queryset = queryset.filter(status=status)
        if type:
            queryset = queryset.filter(type=type)
        if bank_name:
            queryset = queryset.filter(bank_name__icontains=bank_name)
            
        # Apply eager loading
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        
        return queryset
    
    @swagger_auto_schema(
        operation_description="List all IBANs",
        responses={200: IBANSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List all IBANs with optional filtering."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new IBAN",
        request_body=IBANSerializer,
        responses={201: IBANSerializer()}
    )
    def post(self, request, *args, **kwargs):
        """Create a new IBAN."""
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Save the new IBAN and log the creation."""
        iban = serializer.save()
        logger.info(f"IBAN created: {iban.iban}")


class IBANAPIDetailView(viewsets.ModelViewSet):
    """
    API view for retrieving, updating, or deleting an IBAN.
    
    GET: Retrieve an IBAN
    PUT: Update an IBAN
    PATCH: Partially update an IBAN
    DELETE: Delete an IBAN
    """
    queryset = IBAN.objects.all()
    serializer_class = IBANSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve an IBAN",
        responses={200: IBANSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific IBAN."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update an IBAN",
        request_body=IBANSerializer,
        responses={200: IBANSerializer()}
    )
    def update(self, request, *args, **kwargs):
        """Update an IBAN completely."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update an IBAN",
        request_body=IBANSerializer,
        responses={200: IBANSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        """Update an IBAN partially."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete an IBAN",
        responses={204: "No content"}
    )
    def destroy(self, request, *args, **kwargs):
        """Delete an IBAN."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Validate an IBAN",
        responses={200: "IBAN validation result"}
    )
    def validate(self, request, *args, **kwargs):
        """
        Validate the IBAN format and checksum.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: Validation result
        """
        iban = self.get_object()
        is_valid = validate_iban(iban.iban)
        
        return Response({
            "iban": iban.iban,
            "is_valid": is_valid,
            "message": "IBAN is valid" if is_valid else "IBAN is invalid"
        })


class DebtorAPIListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating debtors.
    
    GET: List all debtors
    POST: Create a new debtor
    """
    queryset = Debtor.objects.all()
    serializer_class = DebtorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'iban__iban', 'city', 'country']
    ordering_fields = ['name', 'iban__iban', 'country']
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on query parameters.
        
        Returns:
            QuerySet: Filtered queryset of debtors
        """
        queryset = Debtor.objects.all()
        
        # Apply filters if provided
        country = self.request.query_params.get('country')
        city = self.request.query_params.get('city')
        iban = self.request.query_params.get('iban')
        
        if country:
            queryset = queryset.filter(country=country)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if iban:
            queryset = queryset.filter(iban__iban__icontains=iban)
            
        # Apply eager loading
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        
        return queryset
    
    @swagger_auto_schema(
        operation_description="List all debtors",
        responses={200: DebtorSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List all debtors with optional filtering."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new debtor",
        request_body=DebtorSerializer,
        responses={201: DebtorSerializer()}
    )
    def post(self, request, *args, **kwargs):
        """Create a new debtor."""
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Save the new debtor and log the creation."""
        debtor = serializer.save()
        logger.info(f"Debtor created: {debtor.name}")


class DebtorAPIDetailView(viewsets.ModelViewSet):
    """
    API view for retrieving, updating, or deleting a debtor.
    
    GET: Retrieve a debtor
    PUT: Update a debtor
    PATCH: Partially update a debtor
    DELETE: Delete a debtor
    """
    queryset = Debtor.objects.all()
    serializer_class = DebtorSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve a debtor",
        responses={200: DebtorSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific debtor."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update a debtor",
        request_body=DebtorSerializer,
        responses={200: DebtorSerializer()}
    )
    def update(self, request, *args, **kwargs):
        """Update a debtor completely."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update a debtor",
        request_body=DebtorSerializer,
        responses={200: DebtorSerializer()}
    )
    def partial_update(self, request, *args, **kwargs):
        """Update a debtor partially."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a debtor",
        responses={204: "No content"}
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a debtor."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_description="Get IBANs associated with this debtor",
        responses={200: IBANSerializer(many=True)}
    )
    def ibans(self, request, *args, **kwargs):
        """
        List IBANs associated with this debtor.
        
        Returns the primary IBAN for the debtor.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: List of IBANs
        """
        debtor = self.get_object()
        ibans = [debtor.iban]  # Only one IBAN per debtor in current model
        
        serializer = IBANSerializer(ibans, many=True)
        return Response(serializer.data)


# Web Interface Views
class IBANListView(LoginRequiredMixin, ListView):
    """
    View for displaying a list of IBANs in the web interface.
    """
    model = IBAN
    template_name = 'api/core/iban_list.html'
    context_object_name = 'ibans'
    paginate_by = 10
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on search form.
        
        Returns:
            QuerySet: Filtered queryset of IBANs
        """
        queryset = IBAN.objects.all()
        
        # Get search form
        form = IBANSearchForm(self.request.GET or None)
        
        # Apply filters if form is valid
        if form.is_valid():
            iban = form.cleaned_data.get('iban')
            bank_name = form.cleaned_data.get('bank_name')
            status = form.cleaned_data.get('status')
            type = form.cleaned_data.get('type')
            
            if iban:
                queryset = queryset.filter(iban__icontains=iban)
            if bank_name:
                queryset = queryset.filter(bank_name__icontains=bank_name)
            if status:
                queryset = queryset.filter(status=status)
            if type:
                queryset = queryset.filter(type=type)
                
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add search form and title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = IBANSearchForm(self.request.GET or None)
        context['title'] = _("IBAN Management")
        return context


class IBANCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new IBAN in the web interface.
    """
    model = IBAN
    form_class = IBANForm
    template_name = 'api/core/iban_form.html'
    success_url = reverse_lazy('iban-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title and action to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Create IBAN")
        context['action'] = _("Create")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission with user association.
        
        Args:
            form: The form that was submitted
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("IBAN created successfully"))
        return response


class IBANUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating an existing IBAN in the web interface.
    """
    model = IBAN
    form_class = IBANForm
    template_name = 'api/core/iban_form.html'
    success_url = reverse_lazy('iban-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title and action to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Update IBAN")
        context['action'] = _("Update")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission.
        
        Args:
            form: The form that was submitted
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        messages.success(self.request, _("IBAN updated successfully"))
        return response


class IBANDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting an IBAN in the web interface.
    """
    model = IBAN
    template_name = 'api/core/iban_confirm_delete.html'
    success_url = reverse_lazy('iban-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete IBAN")
        return context
    
    def delete(self, request, *args, **kwargs) -> HttpResponse:
        """
        Handle deletion and show success message.
        
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(self.request, _("IBAN deleted successfully"))
        return super().delete(request, *args, **kwargs)


class DebtorListView(LoginRequiredMixin, ListView):
    """
    View for displaying a list of debtors in the web interface.
    """
    model = Debtor
    template_name = 'api/core/debtor_list.html'
    context_object_name = 'debtors'
    paginate_by = 10
    
    def get_queryset(self) -> QuerySet:
        """
        Filter the queryset based on search form.
        
        Returns:
            QuerySet: Filtered queryset of debtors
        """
        queryset = Debtor.objects.all()
        
        # Get search form
        form = DebtorSearchForm(self.request.GET or None)
        
        # Apply filters if form is valid
        if form.is_valid():
            name = form.cleaned_data.get('name')
            iban = form.cleaned_data.get('iban')
            city = form.cleaned_data.get('city')
            country = form.cleaned_data.get('country')
            
            if name:
                queryset = queryset.filter(name__icontains=name)
            if iban:
                queryset = queryset.filter(iban__iban__icontains=iban)
            if city:
                queryset = queryset.filter(city__icontains=city)
            if country:
                queryset = queryset.filter(country=country)
                
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add search form and title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['search_form'] = DebtorSearchForm(self.request.GET or None)
        context['title'] = _("Debtor Management")
        return context


class DebtorCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new debtor in the web interface.
    """
    model = Debtor
    form_class = DebtorForm
    template_name = 'api/core/debtor_form.html'
    success_url = reverse_lazy('debtor-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title and action to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Create Debtor")
        context['action'] = _("Create")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission with user association.
        
        Args:
            form: The form that was submitted
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _("Debtor created successfully"))
        return response


class DebtorUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating an existing debtor in the web interface.
    """
    model = Debtor
    form_class = DebtorForm
    template_name = 'api/core/debtor_form.html'
    success_url = reverse_lazy('debtor-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title and action to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Update Debtor")
        context['action'] = _("Update")
        return context
    
    def form_valid(self, form) -> HttpResponse:
        """
        Handle successful form submission.
        
        Args:
            form: The form that was submitted
            
        Returns:
            HttpResponse: Redirect to success URL
        """
        response = super().form_valid(form)
        messages.success(self.request, _("Debtor updated successfully"))
        return response


class DebtorDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting a debtor in the web interface.
    """
    model = Debtor
    template_name = 'api/core/debtor_confirm_delete.html'
    success_url = reverse_lazy('debtor-list')
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add title to context.
        
        Returns:
            Dict[str, Any]: Context data
        """
        context = super().get_context_data(**kwargs)
        context['title'] = _("Delete Debtor")
        return context
    
    def delete(self, request, *args, **kwargs) -> HttpResponse:
        """
        Handle deletion and show success message.
        
        Returns:
            HttpResponse: Redirect to success URL
        """
        messages.success(self.request, _("Debtor deleted successfully"))
        return super().delete(request, *args, **kwargs)
"""
Views for the Collection application.

This module defines both API endpoints and web interface views
for managing mandates and collections.
"""
import logging
from typing import Any, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.collection.forms import MandateForm, CollectionForm, MandateSearchForm, CollectionSearchForm
from api.collection.models import Mandate, Collection
from api.collection.serializers import (
    MandateSerializer, MandateListSerializer, MandateDetailSerializer,
    CollectionSerializer, CollectionListSerializer, CollectionCreateSerializer
)

# Configure logger
logger = logging.getLogger(__name__)


# API Views
class MandateAPIListView(generics.ListAPIView):
    """
    API view for listing mandates.
    
    GET: List all mandates
    """
    queryset = Mandate.objects.all()
    serializer_class = MandateListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['debtor_name__name', 'debtor_iban__iban', 'scheme']
    ordering_fields = ['signature_date', 'is_active']
    
    @swagger_auto_schema(
        operation_description="List all mandates",
        responses={200: MandateListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List mandates with optional filtering."""
        return super().get(request, *args, **kwargs)


class MandateAPIDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving a specific mandate.
    
    GET: Retrieve a mandate
    """
    queryset = Mandate.objects.all()
    serializer_class = MandateDetailSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve a mandate",
        responses={200: MandateDetailSerializer()}
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a specific mandate."""
        return super().get(request, *args, **kwargs)


class MandateAPICreateView(generics.CreateAPIView):
    """
    API view for creating a mandate.
    
    POST: Create a mandate
    """
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a mandate",
        request_body=MandateSerializer,
        responses={201: MandateSerializer()}
    )
    def post(self, request, *args, **kwargs):
        """Create a new mandate."""
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Save the new mandate and log the creation."""
        mandate = serializer.save()
        logger.info(f"Mandate created: {mandate.id}")


class MandateAPIUpdateView(generics.UpdateAPIView):
    """
    API view for updating a mandate.
    
    PUT, PATCH: Update a mandate
    """
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update a mandate",
        request_body=MandateSerializer,
        responses={200: MandateSerializer()}
    )
    def put(self, request, *args, **kwargs):
        """Update a mandate completely."""
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update a mandate",
        request_body=MandateSerializer,
        responses={200: MandateSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        """Update a mandate partially."""
        return super().patch(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Save the updated mandate and log the update."""
        mandate = serializer.save()
        logger.info(f"Mandate updated: {mandate.id}")


class MandateAPIDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a mandate.
    
    DELETE: Delete a mandate
    """
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Delete a mandate",
        responses={204: "No content"}
    )
    def delete(self, request, *args, **kwargs):
        """Delete a mandate."""
        return super().delete(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        """Log the deletion and delete the mandate."""
        logger.info(f"Mandate deleted: {instance.id}")
        instance.delete()


class CollectionAPIListView(generics.ListAPIView):
    """
    API view for listing collections.
    
    GET: List all collections or collections for a specific mandate
    """
    serializer_class = CollectionListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['mandate__debtor_name__name', 'status']
    ordering_fields = ['scheduled_date', 'status', 'amount']
    
    def get_queryset(self):
        """
        Get collections, optionally filtered by mandate.
        
        Returns:
            QuerySet: Filtered collection queryset
        """
        mandate_pk = self.kwargs.get('mandate_pk')
        if mandate_pk:
            return Collection.objects.filter(mandate__pk=mandate_pk)
        return Collection.objects.all()
    
    @swagger_auto_schema(
        operation_description="List collections",
        responses={200: CollectionListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        """List collections with optional filtering."""
        return super().get(request, *args, **kwargs)


class CollectionAPIDetailView(generics.RetrieveAPIView):
    """
    API view for retrieving a specific collection.
    
    GET: Retrieve a collection
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Retrieve a collection",
        responses={200: CollectionSerializer()}
    )
    def get(self, request, *args, **kwargs):
        """Retrieve a specific collection."""
        return super().get(request, *args, **kwargs)


class CollectionAPICreateView(generics.CreateAPIView):
    """
    API view for creating a collection.
    
    POST: Create a collection
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionCreateSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a collection",
        request_body=CollectionCreateSerializer,
        responses={201: CollectionSerializer()}
    )
    def post(self, request, *args, **kwargs):
        """Create a new collection."""
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Save the new collection and log the creation."""
        collection = serializer.save()
        logger.info(f"Collection created: {collection.id}")


class CollectionAPIUpdateView(generics.UpdateAPIView):
    """
    API view for updating a collection.
    
    PUT, PATCH: Update a collection
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update a collection",
        request_body=CollectionSerializer,
        responses={200: CollectionSerializer()}
    )
    def put(self, request, *args, **kwargs):
        """Update a collection completely."""
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Partially update a collection",
        request_body=CollectionSerializer,
        responses={200: CollectionSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        """Update a collection partially."""
        return super().patch(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Save the updated collection and log the update."""
        collection = serializer.save()
        logger.info(f"Collection updated: {collection.id}")


class CollectionAPIDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a collection.
    
    DELETE: Delete a collection
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Delete a collection",
        responses={204: "No content"}
    )
    def delete(self, request, *args, **kwargs):
        """Delete a collection."""
        return super().delete(request, *args, **kwargs)
    
    def perform_destroy(self, instance):
        """Log the deletion and delete the collection."""
        logger.info(f"Collection deleted: {instance.id}")
        instance.delete()


class CollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Collection model.
    
    Provides all CRUD operations in a single class.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        Returns:
            Type[serializers.Serializer]: The appropriate serializer class
        """
        if self.action == 'list':
            return CollectionListSerializer
        elif self.action == 'create':
            return CollectionCreateSerializer
        return CollectionSerializer
    
    @swagger_auto_schema(operation_description="Retrieve a collection")
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific collection."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_description="List collections")
    def list(self, request, *args, **kwargs):
        """List all collections."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_description="Create a collection", request_body=CollectionSerializer)
    def create(self, request, *args, **kwargs):
        """Create a new collection."""
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_description="Update a collection", request_body=CollectionSerializer)
    def update(self, request, *args, **kwargs):
        """Update a collection completely."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_description="Partial update of a collection", request_body=CollectionSerializer)
    def partial_update(self, request, *args, **kwargs):
        """Update a collection partially."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_description="Delete a collection")
    def destroy(self, request, *args, **kwargs):
        """Delete a collection."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Custom action to cancel a collection.
        
        Args:
            request: The HTTP request
            pk: The primary key of the collection
            
        Returns:
            Response: Success or error message
        """
        collection = self.get_object()
        if collection.status != 'pending':
            return Response(
                {'detail': _('Only pending collections can be cancelled.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        collection.status = 'cancelled'
        collection.save()
        return Response({'detail': _('Collection cancelled successfully.')})


# Web Views
class MandateListView(ListView):
    """
    View for displaying a list of mandates in the web interface.
    """
    model = Mandate
    template_name = 'api/collection/mandate_list.html'
    context_object_name = 'mandates'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get mandates with optional filtering.
        
        Returns:
            QuerySet: Filtered mandate queryset
        """
        queryset = Mandate.objects.all().order_by('-signature_date')
        
        # Apply filters if provided
        debtor_name = self.request.GET.get('debtor_name')
        debtor_iban = self.request.GET.get('debtor_iban')
        is_active = self.request.GET.get('is_active')
        
        if debtor_name:
            queryset = queryset.filter(debtor_name__name__icontains=debtor_name)
        if debtor_iban:
            queryset = queryset.filter(debtor_iban__iban__icontains=debtor_iban)
        if is_active in ['True', 'False']:
            queryset = queryset.filter(is_active=is_active == 'True')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add search form to context."""
        context = super().get_context_data(**kwargs)
        context['search_form'] = MandateSearchForm(self.request.GET or None)
        context['title'] = _('Mandates')
        return context


class MandateCreateView(CreateView):
    """
    View for creating a new mandate in the web interface.
    """
    model = Mandate
    form_class = MandateForm
    template_name = 'api/collection/mandate_form.html'
    success_url = reverse_lazy('mandate-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Mandate')
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _('Mandate created successfully.'))
        return super().form_valid(form)


class MandateUpdateView(UpdateView):
    """
    View for updating an existing mandate in the web interface.
    """
    model = Mandate
    form_class = MandateForm
    template_name = 'api/collection/mandate_form.html'
    success_url = reverse_lazy('mandate-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Mandate')
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _('Mandate updated successfully.'))
        return super().form_valid(form)


class MandateDeleteView(DeleteView):
    """
    View for deleting a mandate in the web interface.
    """
    model = Mandate
    template_name = 'api/collection/mandate_confirm_delete.html'
    success_url = reverse_lazy('mandate-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Mandate')
        return context
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion and display success message."""
        messages.success(request, _('Mandate deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class CollectionListView(ListView):
    """
    View for displaying a list of collections in the web interface.
    """
    model = Collection
    template_name = 'api/collection/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 10
    
    def get_queryset(self):
        """
        Get collections with optional filtering.
        
        Returns:
            QuerySet: Filtered collection queryset
        """
        queryset = Collection.objects.all().order_by('-scheduled_date')
        
        # Apply filters if provided
        debtor_name = self.request.GET.get('debtor_name')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')
        
        if debtor_name:
            queryset = queryset.filter(mandate__debtor_name__name__icontains=debtor_name)
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add search form to context."""
        context = super().get_context_data(**kwargs)
        context['search_form'] = CollectionSearchForm(self.request.GET or None)
        context['title'] = _('Collections')
        return context


class CollectionCreateView(CreateView):
    """
    View for creating a new collection in the web interface.
    """
    model = Collection
    form_class = CollectionForm
    template_name = 'api/collection/collection_form.html'
    success_url = reverse_lazy('collection-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Collection')
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _('Collection created successfully.'))
        return super().form_valid(form)


class CollectionUpdateView(UpdateView):
    """
    View for updating an existing collection in the web interface.
    """
    model = Collection
    form_class = CollectionForm
    template_name = 'api/collection/collection_form.html'
    success_url = reverse_lazy('collection-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Collection')
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, _('Collection updated successfully.'))
        return super().form_valid(form)


class CollectionDeleteView(DeleteView):
    """
    View for deleting a collection in the web interface.
    """
    model = Collection
    template_name = 'api/collection/collection_confirm_delete.html'
    success_url = reverse_lazy('collection-list')
    
    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Collection')
        return context
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion and display success message."""
        messages.success(request, _('Collection deleted successfully.'))
        return super().delete(request, *args, **kwargs)
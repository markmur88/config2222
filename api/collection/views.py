from rest_framework import generics, viewsets
from api.collection.models import Mandate, Collection
from api.collection.serializers import MandateSerializer, CollectionSerializer
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from api.collection.forms import CollectionForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from api.collection.forms import MandateForm, CollectionForm

class MandateListCreateView(generics.ListCreateAPIView):
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer

class MandateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer

class CollectionListCreateView(generics.ListCreateAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class CollectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    @swagger_auto_schema(operation_description="Retrieve a collection")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="List collections")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Create a collection", request_body=CollectionSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update a collection", request_body=CollectionSerializer)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partial update of a collection", request_body=CollectionSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete a collection")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class MandateListView(ListView):
    model = Mandate
    template_name = 'api/collection/mandate_list.html'
    context_object_name = 'mandates'

class MandateCreateView(CreateView):
    model = Mandate
    form_class = MandateForm
    template_name = 'api/collection/mandate_form.html'
    success_url = reverse_lazy('mandate-list')

class MandateUpdateView(UpdateView):
    model = Mandate
    form_class = MandateForm
    template_name = 'api/collection/mandate_form.html'
    success_url = reverse_lazy('mandate-list')

class MandateDeleteView(DeleteView):
    model = Mandate
    template_name = 'api/collection/mandate_confirm_delete.html'
    success_url = reverse_lazy('mandate-list')

class CollectionListView(ListView):
    model = Collection
    template_name = 'api/collection/collection_list.html'
    context_object_name = 'collections'

class CollectionCreateView(CreateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'api/collection/collection_form.html'
    success_url = reverse_lazy('collection-list')

class CollectionUpdateView(UpdateView):
    model = Collection
    form_class = CollectionForm
    template_name = 'api/collection/collection_form.html'
    success_url = reverse_lazy('collection-list')

class CollectionDeleteView(DeleteView):
    model = Collection
    template_name = 'api/collection/collection_confirm_delete.html'
    success_url = reverse_lazy('collection-list')


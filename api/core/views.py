from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login  # Import necesario para autenticación
from django.urls import reverse, reverse_lazy  # Import necesario para resolver nombres de URL
from django.views.decorators.csrf import csrf_protect  # Import necesario para proteger contra CSRF
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from api.core.serializers import CoreSerializer  # Asegúrate de que CoreSerializer esté definido en serializers.py
from django.contrib import messages  # Import necesario para manejar mensajes
from django.views.generic import TemplateView, RedirectView, CreateView, UpdateView, DeleteView  # Import necesario para vistas basadas en clases
from api.core.forms import IBANForm, DebtorForm
from api.core.models import CoreModel, IBAN, Debtor

# Create your views here.

# class CoreViewSet(viewsets.ModelViewSet):
#     # ...existing code...

#     @swagger_auto_schema(operation_description="Retrieve core data")
#     def retrieve(self, request, *args, **kwargs):
#         return super().retrieve(request, *args, **kwargs)

#     @swagger_auto_schema(operation_description="List core data")
#     def list(self, request, *args, **kwargs):
#         return super().list(request, *args, **kwargs)

#     @swagger_auto_schema(operation_description="Create core data", request_body=CoreSerializer)
#     def create(self, request, *args, **kwargs):
#         return super().create(request, *args, **kwargs)

#     @swagger_auto_schema(operation_description="Update core data", request_body=CoreSerializer)
#     def update(self, request, *args, **kwargs):
#         return super().update(request, *args, **kwargs)

#     @swagger_auto_schema(operation_description="Partial update of core data", request_body=CoreSerializer)
#     def partial_update(self, request, *args, **kwargs):
#         return super().partial_update(request, *args, **kwargs)

#     @swagger_auto_schema(operation_description="Delete core data")
#     def destroy(self, request, *args, **kwargs):
#         return super().destroy(request, *args, **kwargs)

# def core_model_list(request):
#     core_models = CoreModel.objects.all()
#     return render(request, 'api/core/core_model_list.html', {'core_models': core_models})

# def core_model_create(request):
#     if request.method == 'POST':
#         form = CoreModelForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('core-model-list')
#     else:
#         form = CoreModelForm()
#     return render(request, 'api/core/core_model_form.html', {'form': form})

# def core_model_update(request, pk):
#     core_model = get_object_or_404(CoreModel, pk=pk)
#     if request.method == 'POST':
#         form = CoreModelForm(request.POST, instance=core_model)
#         if form.is_valid():
#             form.save()
#             return redirect('core-model-list')
#     else:
#         form = CoreModelForm(instance=core_model)
#     return render(request, 'api/core/core_model_form.html', {'form': form})

# def core_model_delete(request, pk):
#     core_model = get_object_or_404(CoreModel, pk=pk)
#     if request.method == 'POST':
#         core_model.delete()
#         return redirect('core-model-list')
#     return render(request, 'api/core/core_model_confirm_delete.html', {'core_model': core_model})

class IBANListView(TemplateView):
    template_name = 'api/core/iban_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ibans'] = IBAN.objects.all()
        return context

class IBANCreateView(CreateView):
    model = IBAN
    form_class = IBANForm
    template_name = 'api/core/iban_form.html'
    success_url = reverse_lazy('iban-list')

class IBANUpdateView(UpdateView):
    model = IBAN
    form_class = IBANForm
    template_name = 'api/core/iban_form.html'
    success_url = reverse_lazy('iban-list')

class IBANDeleteView(DeleteView):
    model = IBAN
    template_name = 'api/core/iban_confirm_delete.html'
    success_url = reverse_lazy('iban-list')

class DebtorListView(TemplateView):
    template_name = 'api/core/debtor_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['debtors'] = Debtor.objects.all()
        return context

class DebtorCreateView(CreateView):
    model = Debtor
    form_class = DebtorForm
    template_name = 'api/core/debtor_form.html'
    success_url = reverse_lazy('debtor-list')

class DebtorUpdateView(UpdateView):
    model = Debtor
    form_class = DebtorForm
    template_name = 'api/core/debtor_form.html'
    success_url = reverse_lazy('debtor-list')

class DebtorDeleteView(DeleteView):
    model = Debtor
    template_name = 'api/core/debtor_confirm_delete.html'
    success_url = reverse_lazy('debtor-list')
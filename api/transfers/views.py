from rest_framework import generics
from api.transfers.models import SEPA2, SEPA3, SepaTransaction, Transfer
from api.transfers.serializers import SEPA2Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, AllowAny
from api.core.bank_services import deutsche_bank_transfer, memo_bank_transfer
from rest_framework.exceptions import APIException
import logging
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from api.transfers.forms import SEPA2Form
from django.contrib import messages
from api.core.services import generate_sepa_xml
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


logger = logging.getLogger("bank_services")

class TransferVIEWList(generics.ListCreateAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class TransferVIEWDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class TransferVIEWCreateView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer
    
    @swagger_auto_schema(operation_description="Create a transfer", request_body=SEPA2Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)

        existing_transfer = SEPA2.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transfer:
            return Response({"message": "Duplicate transfer", "transfer_id": existing_transfer.id},
                            status=status.HTTP_200_OK)

        serializer = SEPA2Serializer(data=request.data)
        if serializer.is_valid():
            transfer_data = serializer.validated_data
            bank = request.data.get("bank")

            try:
                if bank == "memo":
                    response = memo_bank_transfer(
                        transfer_data["source_account"], transfer_data["destination_account"],
                        transfer_data["amount"], transfer_data["currency"], idempotency_key
                    )
                elif bank == "deutsche":
                    response = deutsche_bank_transfer(
                        transfer_data["source_account"], transfer_data["destination_account"],
                        transfer_data["amount"], transfer_data["currency"], idempotency_key
                    )
                else:
                    return Response({"error": "Invalid bank selection"}, status=status.HTTP_400_BAD_REQUEST)

                if "error" in response:
                    logger.warning(f"Error en la transferencia: {response['error']}")
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

                serializer.save(idempotency_key=idempotency_key, status="ACCP")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.critical(f"Error crítico en la transferencia: {str(e)}", exc_info=True)
                raise APIException("Error inesperado en la transferencia bancaria.")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def transferVIEW_create_view(request):
    if request.method == 'POST':
        form = SEPA2Form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('transfer_list'))
    else:
        try:
            form = SEPA2Form()
        except Exception as e:
            messages.error(request, f"Error al cargar el formulario: {str(e)}")
            form = None
    return render(request, 'api/transfers/transfer_form.html', {'form': form})

def transferVIEW_update_view(request, pk):
    transfer = get_object_or_404(SEPA2, pk=pk)
    if request.method == 'POST':
        form = SEPA2Form(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('transfer_detail', args=[pk]))  # Redirige al detalle de la transferencia
    else:
        form = SEPA2Form(instance=transfer)
    return render(request, 'api/transfers/transfer_form.html', {'form': form})

class SepaTransferVIEWCreateView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

    @swagger_auto_schema(operation_description="Create a SEPA transfer", request_body=SEPA2Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-key")  # Corregido: se usa una cadena literal
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)

        existing_transaction = SEPA2.objects.filter(transaction_id=idempotency_key).first()
        if existing_transaction:
            return Response({"message": "Duplicate SEPA transfer", "transaction_id": existing_transaction.id}, status=status.HTTP_200_OK)

        serializer = SEPA2Serializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.save()
            try:
                sepa_xml = generate_sepa_xml(transaction)
                return Response({"sepa_xml": sepa_xml, "transaction": serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.critical(f"Error generating SEPA XML: {str(e)}", exc_info=True)
                raise APIException("Unexpected error during SEPA transfer.")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SepaTransferVIEWListView(generics.ListAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class SepaTransferVIEWUpdateView(generics.UpdateAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class SepaTransferVIEWDeleteView(generics.DestroyAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

def sepa_transactionVIEW_create_view(request):
    if request.method == 'POST':
        form = SEPA2Form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('sepa-transfer_list'))
    else:
        form = SEPA2Form()
    return render(request, 'transfers/sepa_transaction_form.html', {'form': form})

def sepa_transactionVIEW_update_view(request, pk):
    transaction = get_object_or_404(SEPA2, pk=pk)
    if request.method == 'POST':
        form = SEPA2Form(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('sepa-transaction-detail', args=[pk]))
    else:
        form = SEPA2Form(instance=transaction)
    return render(request, 'transfers/sepa_transaction_form.html', {'form': form})

class SEPA2VIEWList(generics.ListCreateAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class SEPA2VIEWDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer







class TRANSFERLV(ListView):
    model = Transfer
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"

class SEPATRANSACTIONLV(ListView):
    model = SepaTransaction
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"

class SEPA2LV(ListView):
    model = SEPA2
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"

class SEPA3LV(ListView):
    model = SEPA3
    template_name = "api/transfers/transfer_list.html"
    context_object_name = "transfers"


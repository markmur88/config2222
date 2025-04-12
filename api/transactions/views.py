from rest_framework import generics
from api.transfers.serializers import SEPA2Serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import render, get_object_or_404, redirect
from api.transfers.forms import SEPA2Form
from api.transfers.models import SEPA2

class TransactionTRList(generics.ListCreateAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class TransactionTRDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SEPA2.objects.all()
    serializer_class = SEPA2Serializer

class TransactionTRList(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Create a transaction", request_body=SEPA2Serializer)
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar transacción existente por idempotency_key
        existing_transaction = SEPA2.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        
        if existing_transaction:
            return Response({"message": "Duplicate transaction", "transaction_id": existing_transaction.id}, status=status.HTTP_200_OK)
        
        # Crear nueva transacción
        serializer = SEPA2Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                idempotency_key=idempotency_key,
                account=request.user.account  # Vincula automáticamente la cuenta del usuario
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(operation_description="List transactions")
    def get(self, request):
        transactions = SEPA2.objects.filter(account=request.user.account)
        serializer = SEPA2Serializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

def transactionTR_list(request):
    transactions = SEPA2.objects.filter(account=request.user.account)
    return render(request, 'api/transactions/transaction_list.html', {'transactions': transactions})

def transactionTR_create(request):
    if request.method == 'POST':
        form = SEPA2Form(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.account = request.user.account
            transaction.user = request.user
            transaction.save()
            return redirect('transfer_list')
    else:
        form = SEPA2Form()
    return render(request, 'api/transactions/transaction_form.html', {'form': form})

def transactionTR_detail(request, pk):
    # Asegurar que 'pk' sea un UUID válido
    transaction = get_object_or_404(SEPA2, pk=pk, account=request.user.account)
    return render(request, 'api/transactions/transaction_detail.html', {'transaction': transaction})

def transactionTR_update(request, pk):
    transaction = get_object_or_404(SEPA2, pk=pk, account=request.user.account)
    if request.method == 'POST':
        form = SEPA2Form(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            return redirect('transfer_list')
    else:
        form = SEPA2Form(instance=transaction)
    return render(request, 'api/transactions/transaction_form.html', {'form': form})

def transactionTR_delete(request, pk):
    transaction = get_object_or_404(SEPA2, pk=pk, account=request.user.account)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transfer_list')
    return render(request, 'api/transactions/transaction_confirm_delete.html', {'transaction': transaction})


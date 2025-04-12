from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.core.utils import deutsche_bank_request, get_deutsche_bank_accounts, get_memo_bank_accounts, memo_bank_request
from api.core.auth_services import get_deutsche_bank_token, get_memo_bank_token
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from api.sandbox.serializers import IncomingCollectionSerializer
from api.sandbox.services import process_incoming_collection

from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import IncomingCollection
from .forms import IncomingCollectionForm

class BankConnectionTest(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Test Deutsche Bank connection")
    def get(self, request):        
        
        # Prueba Memo Bank
        memo_response = memo_bank_request("test-connection", {})

        # Prueba Deutsche Bank
        db_response = deutsche_bank_request("test-connection", {})
        
        return Response({
            "memo_bank": memo_response,
            "deutsche_bank": db_response
        })

 
class BankAuthView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Get Deutsche Bank token")
    def get(self, request):
        memo_token = get_memo_bank_token().get("access_token")
        deutsche_token = get_deutsche_bank_token().get("access_token")

        memo_accounts = get_memo_bank_accounts(memo_token) if memo_token else {"error": "No token"}
        deutsche_accounts = get_deutsche_bank_accounts(deutsche_token) if deutsche_token else {"error": "No token"}


        return Response({
            "memo_bank_token": memo_token,
            "deutsche_bank_token": deutsche_token
        })


class BankAccountsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Get Deutsche Bank accounts")
    def get(self, request):
        deutsche_token = get_deutsche_bank_token().get("access_token")
        deutsche_accounts = get_deutsche_bank_accounts(deutsche_token) if deutsche_token else {"error": "No token"}

        return Response({
            "deutsche_bank_accounts": deutsche_accounts
        })

class IncomingCollectionView(APIView):
    """
    Endpoint para recibir colecciones entrantes en el sandbox.
    """
    def post(self, request):
        serializer = IncomingCollectionSerializer(data=request.data)
        if serializer.is_valid():
            collection = process_incoming_collection(serializer.validated_data)
            return Response(IncomingCollectionSerializer(collection).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IncomingCollectionListView(ListView):
    model = IncomingCollection
    template_name = 'api/sandbox/incomingcollection_list.html'
    context_object_name = 'collections'

class IncomingCollectionCreateView(CreateView):
    model = IncomingCollection
    form_class = IncomingCollectionForm
    template_name = 'api/sandbox/incomingcollection_form.html'
    success_url = reverse_lazy('incomingcollection-list')

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import get_account_balance, initiate_sepa_transfer

class AccountBalanceView(APIView):
    """
    Endpoint para obtener el balance de una cuenta simulada.
    """
    def get(self, request, account_id):
        balance = get_account_balance(account_id)
        return Response(balance, status=status.HTTP_200_OK)

class SepaTransferView(APIView):
    """
    Endpoint para simular transferencias SEPA.
    """
    def post(self, request):
        response = initiate_sepa_transfer(request.data)
        return Response(response, status=status.HTTP_201_CREATED if "transaction_id" in response else status.HTTP_400_BAD_REQUEST)


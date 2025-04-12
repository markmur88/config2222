from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from api.accounts.models import Account
from api.accounts.serializers import AccountSerializer
from rest_framework.permissions import AllowAny
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from api.accounts.forms import AccountForm
from rest_framework import generics
from rest_framework.permissions import AllowAny
from api.accounts.models import Account
from api.accounts.serializers import AccountSerializer
from django.contrib.auth.mixins import LoginRequiredMixin


class AccountListCreate(generics.ListCreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

class AccountDetailView(generics.RetrieveAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return self.request.user.account  # Obtiene la cuenta del usuario autenticado

    @swagger_auto_schema(operation_description="Retrieve the authenticated user's account")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class AccountListCreateView(generics.ListCreateAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @swagger_auto_schema(
        operation_description="Listar todas las cuentas o crear una nueva cuenta.",
        responses={200: AccountSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Crear una nueva cuenta",
        request_body=AccountSerializer
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)    

class AccountRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    lookup_field = 'id'  # Usamos el campo 'id' como identificador único

    @swagger_auto_schema(operation_description="Retrieve an account")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Update an account", request_body=AccountSerializer)
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Partial update of an account", request_body=AccountSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Delete an account")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

class AccountListView(ListView):
    model = Account
    template_name = 'api/accounts/account_list.html'
    context_object_name = 'accounts'

class AccountCreateView(CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'api/accounts/account_form.html'
    success_url = reverse_lazy('account_list')
    
    def form_valid(self, form):
        # Asocia la cuenta con el usuario actual
        form.instance.user = self.request.user
        return super().form_valid(form)    

class AccountUpdateView(UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'api/accounts/account_form.html'
    success_url = reverse_lazy('account_list')

class AccountDeleteView(DeleteView):
    model = Account
    template_name = 'api/accounts/account_confirm_delete.html'
    success_url = reverse_lazy('account_list')
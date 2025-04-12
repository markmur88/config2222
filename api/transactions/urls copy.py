from django.urls import path
from api.transactions.views import (
    transaction_list,
    transaction_create,
    transaction_detail,
    transaction_update,
    transaction_delete,
    TransactionList,
    TransactionDetail,
)
from api.transactions.views_sepa import SEPAView, TransferListView, TransferCreateView, TransferUpdateView, TransferDeleteView

# Rutas para transacciones
urlpatterns = [
    path('', transaction_list, name='transfer_list'),
    path('create/', transaction_create, name='transaction-create'),
    path('<uuid:pk>/', transaction_detail, name='transaction-detail'),  # Asegurar que acepta UUID
    path('<uuid:pk>/update/', transaction_update, name='transaction-update'),
    path('<uuid:pk>/delete/', transaction_delete, name='transaction-delete'),
    path('api/transactions/', TransactionList.as_view(), name='api-transfer_list'),
    path('api/transactions/<uuid:pk>/', TransactionDetail.as_view(), name='api-transaction-detail'),
]

# Rutas para SEPA
urlpatterns += [
    path('sepa/', TransferListView.as_view(), name='transfer_list'),
    path('sepa/create/', TransferCreateView.as_view(), name='sepa_create'),
    path('sepa/update/<pk>/', TransferUpdateView.as_view(), name='sepa_update'),
    path('sepa/delete/<pk>/', TransferDeleteView.as_view(), name='sepa_delete'),
    path('sepa/api/', SEPAView.as_view(), name='sepa_api'),
]
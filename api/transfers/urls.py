"""
URL configuration for the Transfers application.

This module defines URL patterns for transfer-related views,
including both API endpoints and web interface routes.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.transfers.views import (
    # Standard transfer views
    TransferVIEWList, TransferVIEWDetail, TransferVIEWCreateView,
    transferVIEW_create_view, transferVIEW_update_view,
    
    # SEPA transfer views
    SepaTransferVIEWCreateView, SepaTransferVIEWListView, 
    SepaTransferVIEWUpdateView, SepaTransferVIEWDeleteView,
    
    # SEPA transaction views
    sepa_transactionVIEW_create_view, sepa_transactionVIEW_update_view
)

from api.transfers.views_all import (
    TransferALLCreateView, TransferALLDetail, TransferALLList,
    transferALL_create_view, transferALL_delete_view, 
    transferALL_update_view, transferAllCV
)

from api.transfers.views_copy import (
    TransferCOPYCreateView, SepaTransferCOPYCreateView, TransferCOPYListView,
    TransferCOPY2CreateView, TransferCOPY2UpdateView, TransferCOPY2DeleteView
)

from api.transfers.views_com2 import (
    SEPA3TCOM2CreateView, SEPA3COM2CreateView, SEPA3COM2APIView, SEPA3COM2List,
    # Add ViewSets for router
    SEPA3ViewSet, TransferViewSet
)

from api.transfers.views_api import (
    transfer_api_create_view, transfer_api_view
)

from api.transactions.views import (
    TransactionList, transaction_create
)


# Set up the API router for ViewSets
router = DefaultRouter()
router.register(r'api/sepa3', SEPA3ViewSet, basename='api-sepa3')
router.register(r'api/transfers', TransferViewSet, basename='api-transfer')


# Standard transfer URL patterns
standard_transfer_patterns = [
    path('transfers/', TransferVIEWList.as_view(), name='transfer_list'),
    path('transfers/<uuid:pk>/', TransferVIEWDetail.as_view(), name='transfer_detail'),
    path('transfers/create/', TransferVIEWCreateView.as_view(), name='transfer_create'),
    path('transfers/form/', transferVIEW_create_view, name='transfer_form'),
    path('transfers/form/<uuid:pk>/', transferVIEW_update_view, name='transfer_update'),
]

# SEPA transfer URL patterns
sepa_transfer_patterns = [
    path('sepa-transfers/', SepaTransferVIEWListView.as_view(), name='sepa_transfer_list'),
    path('sepa-transfers/create/', SepaTransferVIEWCreateView.as_view(), name='sepa_transfer_create'),
    path('sepa-transfers/update/<uuid:pk>/', SepaTransferVIEWUpdateView.as_view(), name='sepa_transfer_update'),
    path('sepa-transfers/delete/<uuid:pk>/', SepaTransferVIEWDeleteView.as_view(), name='sepa_transfer_delete'),
    
    # SEPA transaction forms
    path('sepa-transactions/form/', sepa_transactionVIEW_create_view, name='sepa_transaction_form'),
    path('sepa-transactions/form/<uuid:pk>/', sepa_transactionVIEW_update_view, name='sepa_transaction_update'),
]

# Transfer copies URL patterns
transfer_copy_patterns = [
    path('transfers/copy/create/', TransferCOPYCreateView.as_view(), name='transfer_copy_create'),
    path('sepa-transfers/copy/create/', SepaTransferCOPYCreateView.as_view(), name='sepa_transfer_copy_create'),
    path('transfers/copy/list/', TransferCOPYListView.as_view(), name='transfer_copy_list'),
    path('transfers/copy2/create/', TransferCOPY2CreateView.as_view(), name='transfer_copy2_create'),
    path('transfers/copy2/update/<uuid:pk>/', TransferCOPY2UpdateView.as_view(), name='transfer_copy2_update'),
    path('transfers/copy2/delete/<uuid:pk>/', TransferCOPY2DeleteView.as_view(), name='transfer_copy2_delete'),
]

# SEPA3 COM2 URL patterns
sepa3_com2_patterns = [
    path('sepa3-tcom2/create/', SEPA3TCOM2CreateView.as_view(), name='sepa3_tcom2_create'),
    path('sepa3-com2/create/', SEPA3COM2CreateView.as_view(), name='sepa3_com2_create'),
    path('sepa3-com2/api/', SEPA3COM2APIView.as_view(), name='sepa3_com2_api'),
    path('sepa3-com2/list/', SEPA3COM2List.as_view(), name='sepa3_com2_list'),
]

# API URL patterns
api_patterns = [
    path('api/transfers/create/', transfer_api_create_view, name='api_transfer_create'),
    path('api/transfers/', transfer_api_view, name='api_transfer'),
]

# Specialized transfer URL patterns
specialized_transfer_patterns = [
    # Quick transfers
    path('transfers/quick/', TransferVIEWList.as_view(), name='transfer_quick_list'),
    path('transfers/quick/create/', TransferVIEWCreateView.as_view(), name='transfer_quick_create'),
    
    # International transfers
    path('transfers/international/', TransferVIEWList.as_view(), name='transfer_international_list'),
    path('transfers/international/create/', TransferVIEWCreateView.as_view(), name='transfer_international_create'),
]

# 'All' transfers URL patterns
transfer_all_patterns = [
    path('transfers/all/', TransferALLList.as_view(), name='transfer_all_list'),
    path('transfers/all/<uuid:pk>/', TransferALLDetail.as_view(), name='transfer_all_detail'),
    path('transfers/all/create/', TransferALLCreateView.as_view(), name='transfer_all_create'),
    path('transfers/all/form/', transferALL_create_view, name='transfer_all_form'),
    path('transfers/all/form2/', transferAllCV.as_view(), name='transferAllCV'),
    path('transfers/all/form/<uuid:pk>/', transferALL_update_view, name='transfer_all_update'),
    path('transfers/all/delete/<uuid:pk>/', transferALL_delete_view, name='transfer_all_delete'),
]

# Transaction-specific URL patterns
transaction_patterns = [
    # Quick transactions
    path('transactions/quick/', TransactionList.as_view(), name='transaction_quick_list'),
    path('transactions/quick/create/', transaction_create, name='transaction_quick_create'),
    
    # International transactions
    path('transactions/international/', TransactionList.as_view(), name='transaction_international_list'),
    path('transactions/international/create/', transaction_create, name='transaction_international_create'),
]

# Combine all patterns
urlpatterns = (
    standard_transfer_patterns +
    sepa_transfer_patterns +
    transfer_copy_patterns +
    sepa3_com2_patterns +
    api_patterns +
    specialized_transfer_patterns +
    transfer_all_patterns +
    transaction_patterns
)

# Include router URLs
urlpatterns += [
    path('', include(router.urls)),
]
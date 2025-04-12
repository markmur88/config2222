from django.urls import path
from api.transfers.views import (
    TransferVIEWList, TransferVIEWDetail, TransferVIEWCreateView,
    SepaTransferVIEWCreateView, SepaTransferVIEWListView, SepaTransferVIEWUpdateView,
    SepaTransferVIEWDeleteView, transferVIEW_create_view, transferVIEW_update_view,
    sepa_transactionVIEW_create_view, sepa_transactionVIEW_update_view
)
from api.transfers.views_all import TransferALLCreateView, TransferALLDetail, TransferALLList, transferALL_create_view, transferALL_delete_view, transferALL_update_view, transferAllCV
from api.transfers.views_copy import (
    TransferCOPYCreateView, SepaTransferCOPYCreateView, TransferCOPYListView,
    TransferCOPY2CreateView, TransferCOPY2UpdateView, TransferCOPY2DeleteView
)
from api.transfers.views_com2 import (
    SEPA3TCOM2CreateView, SEPA3COM2CreateView, SEPA3COM2APIView, SEPA3COM2List
)
from api.transfers.views_api import (
    transfer_api_create_view, transfer_api_view
)
from api.transactions.views import (
    TransactionTRList, transactionTR_create
)

# Clasificación de URLs
urlpatterns = [
    # Transferencias generales
    path('transfers/', TransferVIEWList.as_view(), name='transfer_list'),
    path('transfers/<int:pk>/', TransferVIEWDetail.as_view(), name='transfer_detail'),
    path('transfers/create/', TransferVIEWCreateView.as_view(), name='transfer_create'),
    path('transfers/form/', transferVIEW_create_view, name='transfer_form'),
    path('transfers/form/<int:pk>/', transferVIEW_update_view, name='transfer_update'),

    # Transferencias SEPA
    path('sepa-transfers/', SepaTransferVIEWListView.as_view(), name='sepa_transfer_list'),
    path('sepa-transfers/create/', SepaTransferVIEWCreateView.as_view(), name='sepa_transfer_create'),
    path('sepa-transfers/update/<int:pk>/', SepaTransferVIEWUpdateView.as_view(), name='sepa_transfer_update'),
    path('sepa-transfers/delete/<int:pk>/', SepaTransferVIEWDeleteView.as_view(), name='sepa_transfer_delete'),

    # Transacciones SEPA
    path('sepa-transactions/form/', sepa_transactionVIEW_create_view, name='sepa_transaction_form'),
    path('sepa-transactions/form/<int:pk>/', sepa_transactionVIEW_update_view, name='sepa_transaction_update'),

    # Copias de transferencias
    path('transfers/copy/create/', TransferCOPYCreateView.as_view(), name='transfer_copy_create'),
    path('sepa-transfers/copy/create/', SepaTransferCOPYCreateView.as_view(), name='sepa_transfer_copy_create'),
    path('transfers/copy/list/', TransferCOPYListView.as_view(), name='transfer_copy_list'),
    path('transfers/copy2/create/', TransferCOPY2CreateView.as_view(), name='transfer_copy2_create'),
    path('transfers/copy2/update/<int:pk>/', TransferCOPY2UpdateView.as_view(), name='transfer_copy2_update'),
    path('transfers/copy2/delete/<int:pk>/', TransferCOPY2DeleteView.as_view(), name='transfer_copy2_delete'),

    # SEPA3 COM2
    path('sepa3-tcom2/create/', SEPA3TCOM2CreateView.as_view(), name='sepa3_tcom2_create'),
    path('sepa3-com2/create/', SEPA3COM2CreateView.as_view(), name='sepa3_com2_create'),
    path('sepa3-com2/api/', SEPA3COM2APIView.as_view(), name='sepa3_com2_api'),
    path('sepa3-com2/list/', SEPA3COM2List.as_view(), name='sepa3_com2_list'),

    # API de transferencias
    path('api/transfers/create/', transfer_api_create_view, name='api_transfer_create'),
    path('api/transfers/', transfer_api_view, name='api_transfer'),

    # Transferencias rápidas
    path('transfers/quick/', TransferVIEWList.as_view(), name='transfer_quick_list'),
    path('transfers/quick/create/', TransferVIEWCreateView.as_view(), name='transfer_quick_create'),

    # Transferencias internacionales
    path('transfers/international/', TransferVIEWList.as_view(), name='transfer_international_list'),
    path('transfers/international/create/', TransferVIEWCreateView.as_view(), name='transfer_international_create'),

    # Transferencias ALL
    path('transfers/all/', TransferALLList.as_view(), name='transfer_all_list'),
    path('transfers/all/<int:pk>/', TransferALLDetail.as_view(), name='transfer_all_detail'),
    path('transfers/all/create/', TransferALLCreateView.as_view(), name='transfer_all_create'),
    path('transfers/all/form/', transferALL_create_view, name='transfer_all_form'),
    path('transfers/all/form2/', transferAllCV.as_view(), name='transferAllCV'),
    path('transfers/all/form/<int:pk>/', transferALL_update_view, name='transfer_all_update'),
    path('transfers/all/delete/<int:pk>/', transferALL_delete_view, name='transfer_all_delete'),

    # Nuevas URLs para transacciones rápidas
    path('transactions/quick/', TransactionTRList.as_view(), name='transaction_quick_list'),
    path('transactions/quick/create/', transactionTR_create, name='transaction_quick_create'),

    # Nuevas URLs para transacciones internacionales
    path('transactions/international/', TransactionTRList.as_view(), name='transaction_international_list'),
    path('transactions/international/create/', transactionTR_create, name='transaction_international_create'),
]

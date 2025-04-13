from django.urls import path
from api.sct.process_transfer import ProcessTransferView12
from api.sct.views import (
    DownloadPdfView,
    SepaCreditTransferCreateView,
    SepaCreditTransferCreateView2,
    SepaCreditTransferDetailsView,
    SepaCreditTransferStatusView,
    SepaCreditTransferCancelView,
    SepaCreditTransferUpdateScaView,
    SepaCreditTransferListView,
    SepaCreditTransferDownloadXmlView,
    SepaCreditTransferDownloadPdfView,
    SCTList5View,
    SCTProc5View
)
from api.sct.services import SCTCreateView, SCTList, SCTView, SepaCreditTransferCreateView3, SCTLView

urlpatterns = [
    path('', SepaCreditTransferCreateView.as_view(), name='create_sepa_credit_transfer'),
    path('', SepaCreditTransferCreateView2.as_view(), name='create_sepa_credit_transfer2'),
    path('<uuid:payment_id>/', SepaCreditTransferDetailsView.as_view(), name='get_sepa_credit_transfer_details'),
    path('<uuid:payment_id>/status/', SepaCreditTransferStatusView.as_view(), name='get_sepa_credit_transfer_status'),
    path('<uuid:payment_id>/cancel/', SepaCreditTransferCancelView.as_view(), name='cancel_sepa_credit_transfer'),
    path('<uuid:payment_id>/update-sca/', SepaCreditTransferUpdateScaView.as_view(), name='update_sca_sepa_credit_transfer'),
    
    path('list/', SepaCreditTransferListView.as_view(), name='list_sepa_credit_transfers'),
    
    path('<uuid:payment_id>/download-xml/', SepaCreditTransferDownloadXmlView.as_view(), name='download_sepa_credit_transfer_xml'),
    path('<uuid:payment_id>/download-pdf/', SepaCreditTransferDownloadPdfView.as_view(), name='download_sepa_credit_transfer_pdf'),
    
    # SERVICES
    path('list0/', SCTCreateView.as_view(), name='sct_list0'),
    path('list1/', SCTList.as_view(), name='sct_list1'),
    path('list2/', SCTView.as_view(), name='sct_list2'),
    path('list3/', SepaCreditTransferCreateView3.as_view(), name='sct_list3'),
    path('list4/', SCTLView.as_view(), name='sct_list4'),
    
    # HTML SERVICES
    path('list5/', SCTList5View.as_view(), name='sct_list5'),
    path('download-pdf/<int:id>/', DownloadPdfView.as_view(), name='download_pdf'),
    path('proc5/<uuid:pk>/', SCTProc5View.as_view(), name='sct_proc5'),
    path('process/<uuid:idempotency_key>/', ProcessTransferView12.as_view(), name='process_transfer'),
    
]

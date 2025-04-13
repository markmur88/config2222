"""
URL configuration for SEPA Credit Transfer API endpoints.

This module defines all URL patterns for the SEPA Credit Transfer
API endpoints, organized by functionality.
"""
from django.urls import path
from typing import List

from api.sct.views import (
    CancelTransferView,
    DownloadPdfView,
    DownloadXmlView,
    SepaCreditTransferCreateView,
    SepaCreditTransferCreateView2,
    SepaCreditTransferDetailsView,
    SepaCreditTransferStatusView,
    SepaCreditTransferCancelView,
    SepaCreditTransferUpdateScaView,
    SepaCreditTransferListView,
    SepaCreditTransferDownloadXmlView,
    SepaCreditTransferDownloadPdfView,
    SCTList5View
)
from api.sct.services import (
    SCTCreateView,
    SCTList,
    SCTView,
    SepaCreditTransferCreateView3,
    SCTLView
)

# Core API Endpoints
core_urlpatterns = [
    # Base SEPA Credit Transfer endpoints
    path('', SepaCreditTransferCreateView.as_view(), name='create_sepa_credit_transfer'),
    path('v2/', SepaCreditTransferCreateView2.as_view(), name='create_sepa_credit_transfer2'),
    path('list/', SepaCreditTransferListView.as_view(), name='list_sepa_credit_transfers'),
    
    # Detail operations
    path('<uuid:payment_id>/', SepaCreditTransferDetailsView.as_view(), name='get_sepa_credit_transfer_details'),
    path('<uuid:payment_id>/status/', SepaCreditTransferStatusView.as_view(), name='get_sepa_credit_transfer_status'),
    path('<uuid:payment_id>/cancel/', SepaCreditTransferCancelView.as_view(), name='cancel_sepa_credit_transfer'),
    path('<uuid:payment_id>/update-sca/', SepaCreditTransferUpdateScaView.as_view(), name='update_sca_sepa_credit_transfer'),
    
    # File download endpoints
    path('<uuid:payment_id>/download-xml/', SepaCreditTransferDownloadXmlView.as_view(), name='download_sepa_credit_transfer_xml'),
    path('<uuid:payment_id>/download-pdf/', SepaCreditTransferDownloadPdfView.as_view(), name='download_sepa_credit_transfer_pdf'),
]

# Service API Endpoints
service_urlpatterns = [
    path('list0/', SCTCreateView.as_view(), name='sct_list0'),
    path('list1/', SCTList.as_view(), name='sct_list1'),
    path('list2/', SCTView.as_view(), name='sct_list2'),
    path('list3/', SepaCreditTransferCreateView3.as_view(), name='sct_list3'),
    path('list4/', SCTLView.as_view(), name='sct_list4'),
]

# HTML Service Endpoints
html_urlpatterns = [
    path('list5/', SCTList5View.as_view(), name='sct_list5'),
    path('download-xml/<uuid:idempotency_key>/', DownloadXmlView.as_view(), name='download_xml'),
    path('download-pdf/<int:id>/', DownloadPdfView.as_view(), name='download_pdf'),
    path('cancel-transfer/<int:id>/', CancelTransferView.as_view(), name='cancel_transfer'),
]

# Combined URL patterns
urlpatterns = core_urlpatterns + service_urlpatterns + html_urlpatterns
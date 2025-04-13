"""
URL configuration for the SEPA Payment application.

This module defines URL patterns for SEPA payment-related views,
including endpoints for creating, viewing, and checking the status of transfers.
"""
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from api.sepa_payment import views

app_name = 'sepa_payment_api'
app_name = 'sepa_payment'

# Web interface URL patterns
web_urlpatterns = [
    path('', views.index, name='index_sepa_payment'),
    path('transfer/', views.create_transfer, name='create_transfer'),
    path('transfer/<str:payment_id>/status/', views.transfer_status, name='transfer_status'),
    path('transfers/', views.list_transfers, name='list_transfers'),
]

# API URL patterns
api_urlpatterns = [
    path('api/transfers/', views.TransferListCreateAPIView.as_view(), name='api_transfers_list'),
    path('api/transfers/<str:payment_id>/', views.TransferRetrieveAPIView.as_view(), name='api_transfer_detail'),
    path('api/transfers/<str:payment_id>/status/', views.TransferStatusAPIView.as_view(), name='api_transfer_status'),
]

# Apply format suffix patterns to API URLs (allows .json, .api extensions)
api_urlpatterns = format_suffix_patterns(api_urlpatterns)

# Combined URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns
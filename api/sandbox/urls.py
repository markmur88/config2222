"""
URL configuration for the Sandbox application.

This module defines URL patterns for sandbox-related views,
including API endpoints for simulation and web interface views.
"""
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from typing import List

from api.sandbox.views import (
    # API Views
    BankConnectionTest,
    IncomingCollectionAPIView,
    IncomingCollectionDetailAPIView,
    AccountBalanceView,
    SepaTransferView,
    SandboxBankAccountAPIView,
    SandboxBankAccountDetailAPIView,
    SandboxTransactionAPIView,
    SandboxTransactionDetailAPIView,
    
    # Web Interface Views
    IncomingCollectionListView,
    IncomingCollectionCreateView,
    IncomingCollectionUpdateView,
    IncomingCollectionDeleteView,
    SandboxDashboardView,
    SandboxSettingsView
)


# API URL patterns
api_urlpatterns = [
    # Bank connection test endpoints
    path("api/test-banks/", BankConnectionTest.as_view(), name="test-banks"),
    
    # Incoming collections API endpoints
    path("api/incoming-collections/", IncomingCollectionAPIView.as_view(), name="api-incoming-collections"),
    path("api/incoming-collections/<uuid:pk>/", IncomingCollectionDetailAPIView.as_view(), name="api-incoming-collection-detail"),
    path("api/incoming-collections/<uuid:pk>/approve/", 
         IncomingCollectionDetailAPIView.as_view(actions={'post': 'approve'}), name="api-incoming-collection-approve"),
    
    # Account balance API endpoints
    path("api/accounts/<str:account_id>/balance/", AccountBalanceView.as_view(), name="api-account-balance"),
    
    # SEPA transfer API endpoints
    path("api/sepa/transfer/", SepaTransferView.as_view(), name="api-sepa-transfer"),
    path("api/sepa/transfer/<str:transaction_id>/status/", 
         SepaTransferView.as_view(actions={'get': 'status'}), name="api-sepa-transfer-status"),
    
    # Sandbox bank account API endpoints
    path("api/accounts/", SandboxBankAccountAPIView.as_view(), name="api-accounts"),
    path("api/accounts/<uuid:pk>/", SandboxBankAccountDetailAPIView.as_view(), name="api-account-detail"),
    path("api/accounts/<uuid:pk>/transactions/", 
         SandboxBankAccountDetailAPIView.as_view(actions={'get': 'transactions'}), name="api-account-transactions"),
    
    # Sandbox transaction API endpoints
    path("api/transactions/", SandboxTransactionAPIView.as_view(), name="api-transactions"),
    path("api/transactions/<uuid:pk>/", SandboxTransactionDetailAPIView.as_view(), name="api-transaction-detail"),
]

# Apply format suffix patterns to API URLs (allows .json, .api extensions)
api_urlpatterns = format_suffix_patterns(api_urlpatterns)

# Web interface URL patterns
web_urlpatterns = [
    # Dashboard and settings
    path("", SandboxDashboardView.as_view(), name="sandbox-dashboard"),
    path("settings/", SandboxSettingsView.as_view(), name="sandbox-settings"),
    
    # Incoming collections web views
    path("incoming-collections/", IncomingCollectionListView.as_view(), name="incoming-collections"),
    path("incoming-collections/create/", IncomingCollectionCreateView.as_view(), name="incoming-collection-create"),
    path("incoming-collections/<uuid:pk>/update/", IncomingCollectionUpdateView.as_view(), name="incoming-collection-update"),
    path("incoming-collections/<uuid:pk>/delete/", IncomingCollectionDeleteView.as_view(), name="incoming-collection-delete"),
]

# Combined URL patterns
urlpatterns = api_urlpatterns + web_urlpatterns
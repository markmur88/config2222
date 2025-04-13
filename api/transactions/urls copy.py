"""
URL configuration for the Transactions application.

This module defines URL patterns for transaction-related views,
including both web interface routes and API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from api.transactions.views import (
    # Web interface views
    transaction_list,
    transaction_create,
    transaction_detail,
    transaction_update,
    transaction_delete,
    
    # API views
    TransactionList,
    TransactionDetail,
    TransactionViewSet
)
from api.transactions.views_sepa import (
    # Web interface views
    TransferListView,
    TransferCreateView,
    TransferUpdateView,
    TransferDeleteView,
    
    # API views
    SEPAViewSet,
    SEPAView
)


# Set up the router for ViewSets
router = DefaultRouter()
router.register(r'api/transactions', TransactionViewSet, basename='api-transaction')
router.register(r'api/sepa', SEPAViewSet, basename='api-sepa')

# Standard Transaction URL patterns (web interface)
transaction_patterns = [
    path('', transaction_list, name='transaction_list'),
    path('create/', transaction_create, name='transaction_create'),
    path('<uuid:pk>/', transaction_detail, name='transaction_detail'),
    path('<uuid:pk>/update/', transaction_update, name='transaction_update'),
    path('<uuid:pk>/delete/', transaction_delete, name='transaction_delete'),
]

# SEPA Transfer URL patterns (web interface)
sepa_patterns = [
    path('sepa/', TransferListView.as_view(), name='sepa_list'),
    path('sepa/create/', TransferCreateView.as_view(), name='sepa_create'),
    path('sepa/<uuid:pk>/update/', TransferUpdateView.as_view(), name='sepa_update'),
    path('sepa/<uuid:pk>/delete/', TransferDeleteView.as_view(), name='sepa_delete'),
]

# Non-ViewSet API URL patterns
api_patterns = [
    path('api/transactions/', TransactionList.as_view(), name='api_transaction_list'),
    path('api/transactions/<uuid:pk>/', TransactionDetail.as_view(), name='api_transaction_detail'),
    path('api/sepa/', SEPAView.as_view(), name='api_sepa_list'),
]

# Apply format suffix patterns to API URLs (allows .json, .api extensions)
api_patterns = format_suffix_patterns(api_patterns)

# Combine all URL patterns
urlpatterns = transaction_patterns + sepa_patterns + api_patterns

# Include router URLs
urlpatterns += [
    path('', include(router.urls)),
]
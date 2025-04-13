"""
URL configuration for the Transactions application.

This module defines URL patterns for transaction-related views,
including both API endpoints and web interface routes.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.transactions.views import (
    # Function-based views for web interface
    transaction_list,
    transaction_detail,
    transaction_create,
    transaction_update,
    transaction_delete,
    
    # Class-based views for API
    TransactionList,
    TransactionDetail,
    TransactionViewSet,
)

# Create a router for the ViewSet
router = DefaultRouter()
router.register(r'viewset', TransactionViewSet, basename='transaction-viewset')

# URL patterns for web interface
web_urlpatterns = [
    path('', transaction_list, name='transaction_list'),
    path('create/', transaction_create, name='transaction_create'),
    path('<uuid:pk>/', transaction_detail, name='transaction_detail'),
    path('<uuid:pk>/update/', transaction_update, name='transaction_update'),
    path('<uuid:pk>/delete/', transaction_delete, name='transaction_delete'),
]

# URL patterns for API
api_urlpatterns = [
    path('api/', TransactionList.as_view(), name='api_transaction_list'),
    path('api/<uuid:pk>/', TransactionDetail.as_view(), name='api_transaction_detail'),
    path('api/', include(router.urls)),
]

# Combined URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns
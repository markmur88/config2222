"""
URL configuration for the Core application.
This module defines URL patterns for core application views,
including both web interface and API endpoints for IBAN and debtor management.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from typing import List

from api.core.views import (
    # Web interface views
    IBANListView, IBANCreateView, IBANUpdateView, IBANDeleteView,
    DebtorListView, DebtorCreateView, DebtorUpdateView, DebtorDeleteView,
    # API views
    IBANAPIListCreateView, IBANAPIDetailView,
    DebtorAPIListCreateView, DebtorAPIDetailView,
    CoreHealthCheckView,
)

# Web interface URL patterns
web_urlpatterns = [
    # IBAN management web views
    path('ibans/', IBANListView.as_view(), name='iban-list'),
    path('ibans/create/', IBANCreateView.as_view(), name='iban-create'),
    path('ibans/<uuid:pk>/update/', IBANUpdateView.as_view(), name='iban-update'),
    path('ibans/<uuid:pk>/delete/', IBANDeleteView.as_view(), name='iban-delete'),
    
    # Debtor management web views
    path('debtors/', DebtorListView.as_view(), name='debtor-list'),
    path('debtors/create/', DebtorCreateView.as_view(), name='debtor-create'),
    path('debtors/<uuid:pk>/update/', DebtorUpdateView.as_view(), name='debtor-update'),
    path('debtors/<uuid:pk>/delete/', DebtorDeleteView.as_view(), name='debtor-delete'),
]

# Set up routers for ViewSets
router = DefaultRouter()
router.register(r'api/ibans', IBANAPIDetailView, basename='api-iban')
router.register(r'api/debtors', DebtorAPIDetailView, basename='api-debtor')

# API URL patterns for non-viewset views
api_urlpatterns = [
    # Health check endpoint
    path('api/health/', CoreHealthCheckView.as_view(), name='api-health-check'),
    
    # IBAN management API endpoints for non-viewset views
    path('api/ibans/', IBANAPIListCreateView.as_view(), name='api-iban-list-create'),
    
    # Debtor management API endpoints for non-viewset views
    path('api/debtors/', DebtorAPIListCreateView.as_view(), name='api-debtor-list-create'),
]

# Apply format suffix patterns to API URLs (allows .json, .api extensions)
api_urlpatterns = format_suffix_patterns(api_urlpatterns)

# Combined URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns + router.urls
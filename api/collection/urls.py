"""
URL configuration for the Collection application.

This module defines URL patterns for collection-related views,
including both API endpoints and web interface views for managing
mandates and collections.
"""
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from typing import List

from api.collection.views import (
    # Web views
    MandateListView, MandateCreateView, MandateUpdateView, MandateDeleteView,
    CollectionListView, CollectionCreateView, CollectionUpdateView, CollectionDeleteView,
    
    # API views
    MandateAPIListView, MandateAPIDetailView, MandateAPICreateView, MandateAPIUpdateView, MandateAPIDeleteView,
    CollectionAPIListView, CollectionAPIDetailView, CollectionAPICreateView, CollectionAPIUpdateView, CollectionAPIDeleteView,
)


# Web interface URL patterns
web_urlpatterns = [
    # Mandate web views
    path('mandates/', MandateListView.as_view(), name='mandate-list'),
    path('mandates/create/', MandateCreateView.as_view(), name='mandate-create'),
    path('mandates/<uuid:pk>/update/', MandateUpdateView.as_view(), name='mandate-update'),
    path('mandates/<uuid:pk>/delete/', MandateDeleteView.as_view(), name='mandate-delete'),
    
    # Collection web views
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/create/', CollectionCreateView.as_view(), name='collection-create'),
    path('collections/<uuid:pk>/update/', CollectionUpdateView.as_view(), name='collection-update'),
    path('collections/<uuid:pk>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
]

# API URL patterns
api_urlpatterns = [
    # Mandate API endpoints
    path('api/mandates/', MandateAPIListView.as_view(), name='mandate-api-list'),
    path('api/mandates/<uuid:pk>/', MandateAPIDetailView.as_view(), name='mandate-api-detail'),
    path('api/mandates/create/', MandateAPICreateView.as_view(), name='mandate-api-create'),
    path('api/mandates/<uuid:pk>/update/', MandateAPIUpdateView.as_view(), name='mandate-api-update'),
    path('api/mandates/<uuid:pk>/delete/', MandateAPIDeleteView.as_view(), name='mandate-api-delete'),
    
    # Collection API endpoints
    path('api/collections/', CollectionAPIListView.as_view(), name='collection-api-list'),
    path('api/collections/<uuid:pk>/', CollectionAPIDetailView.as_view(), name='collection-api-detail'),
    path('api/collections/create/', CollectionAPICreateView.as_view(), name='collection-api-create'),
    path('api/collections/<uuid:pk>/update/', CollectionAPIUpdateView.as_view(), name='collection-api-update'),
    path('api/collections/<uuid:pk>/delete/', CollectionAPIDeleteView.as_view(), name='collection-api-delete'),
    
    # Additional API endpoints
    path('api/mandates/<uuid:mandate_pk>/collections/', 
         CollectionAPIListView.as_view(), name='mandate-collections-api-list'),
]

# Apply format suffix patterns to API URLs (allows .json, .api extensions)
api_urlpatterns = format_suffix_patterns(api_urlpatterns)

# Combined URL patterns
urlpatterns = web_urlpatterns + api_urlpatterns
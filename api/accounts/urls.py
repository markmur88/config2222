"""
URL configuration for the Accounts application.

This module defines URL patterns for account-related views,
including both API endpoints and web interface views.
"""
from django.urls import path
from typing import List

from api.accounts.views import (
    # API views
    AccountListCreate,
    AccountDetail,
    
    # Web interface views
    AccountListView,
    AccountCreateView,
    AccountUpdateView,
    AccountDeleteView
)


# API URL patterns
api_urlpatterns = [
    path('api/', AccountListCreate.as_view(), name='account-list-create'),
    path('api/<int:pk>/', AccountDetail.as_view(), name='account-detail'),
]

# Web interface URL patterns
web_urlpatterns = [
    path('', AccountListView.as_view(), name='account_list'),
    path('create/', AccountCreateView.as_view(), name='account_create'),
    path('<uuid:pk>/update/', AccountUpdateView.as_view(), name='account_update'),
    path('<uuid:pk>/delete/', AccountDeleteView.as_view(), name='account_delete'),
]

# Combined URL patterns
urlpatterns = api_urlpatterns + web_urlpatterns
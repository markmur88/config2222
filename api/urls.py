"""
URL configuration for the API application.

This module defines the URL routes for the entire API application,
including both web views and API endpoints.
"""
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from api.views import (
    # Core application views
    HomeView,
    LoginView,
    DashboardView,
    LogoutView,
    # Index views for different modules
    AuthIndexView,
    CoreIndexView,
    AccountsIndexView,
    SCTIndexView,
    TransactionsIndexView,
    TransfersIndexView,
    CollectionIndexView
)


# Create schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Bank Services API",
        default_version='v1',
        description="API for bank services including transfers, collections, and account management",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)


# Main application routes
main_urlpatterns = [
    # Authentication and home pages
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('app/dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Module index pages
    path('app/api/auth/index.html', AuthIndexView.as_view(), name='auth_index'),
    path('app/core/index.html', CoreIndexView.as_view(), name='core_index'),
    path('app/accounts/index.html', AccountsIndexView.as_view(), name='accounts_index'),
    path('app/transactions/index.html', TransactionsIndexView.as_view(), name='transactions_index'),
    path('app/transfers/index.html', TransfersIndexView.as_view(), name='transfers_index'),
    path('app/collection/index.html', CollectionIndexView.as_view(), name='collection_index'),
    path('app/sct/index.html', SCTIndexView.as_view(), name='sct_index'),
]


# API documentation routes
api_doc_urlpatterns = [
    path('api/swagger<str:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


# Include routes from all app modules
module_urlpatterns = [
    # Authentication
    path('api/auth/', include('api.authentication.urls')),
    
    # Core functionality
    path('api/core/', include('api.core.urls')),
    
    # Accounts
    path('api/accounts/', include('api.accounts.urls')),
    
    # Transactions
    path('api/transactions/', include('api.transactions.urls')),
    
    # Transfers
    path('api/transfers/', include('api.transfers.urls')),
    
    # Collections
    path('api/collection/', include('api.collection.urls')),
    
    # SEPA Credit Transfers
    path('api/sct/', include('api.sct.urls')),
    
    # SEPA Payments
    path('api/sepa-payment/', include('api.sepa_payment.urls')),
]


# Combine all URL patterns
urlpatterns = main_urlpatterns + api_doc_urlpatterns + module_urlpatterns


# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
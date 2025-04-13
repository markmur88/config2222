"""
URL configuration for the entire project.

This module defines the root URL patterns for the entire application,
including API endpoints, admin interface, and documentation.

For more information on Django URL configuration, see:
https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# API Documentation Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Banking API",
        default_version='v1',
        description="API documentation for the Banking Platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)


# Main URL patterns
urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls, name='admin'),
    
    # API Documentation
    path('api/swagger<str:format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints - Remove the namespaces since app_name is not set
    path('api/auth/', include('api.authentication.urls')),
    path('api/core/', include('api.core.urls')),
    path('api/accounts/', include('api.accounts.urls')),
    path('api/transactions/', include('api.transactions.urls')),
    path('api/transfers/', include('api.transfers.urls')),
    path('api/collection/', include('api.collection.urls')),
    path('api/sct/', include('api.sct.urls')),
    path('api/sepa-payment/', include('api.sepa_payment.urls', namespace='sepa_payment_api')),
    
    # Web Application URLs - Use different URL path prefixes
    path('app/core/', include('api.core.urls')),
    path('app/accounts/', include('api.accounts.urls')),
    path('app/transfers/', include('api.transfers.urls')),
    path('app/collection/', include('api.collection.urls')),
    path('app/sct/', include('api.sct.urls')),
    path('app/sepa-payment/', include('api.sepa_payment.urls', namespace='sepa_payment_web')),
    
    # Root path and other general routes
    path('', include('api.urls')),
    
    # Redirect /swagger to /api/swagger for backward compatibility
    path('swagger/', RedirectView.as_view(url='/api/swagger/', permanent=True)),
    path('redoc/', RedirectView.as_view(url='/api/redoc/', permanent=True)),
]


# Development-specific URL patterns
if settings.DEBUG:
    # Debug Toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    
    # Serve media and static files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add development-specific API documentation with relaxed permissions
    dev_schema_view = get_schema_view(
        openapi.Info(
            title="Banking API (Development)",
            default_version='v1',
            description="Development API documentation with unrestricted access",
            terms_of_service="https://www.example.com/terms/",
            contact=openapi.Contact(email="contact@example.com"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    
    urlpatterns += [
        path('dev/swagger/', dev_schema_view.with_ui('swagger', cache_timeout=0), name='dev-swagger'),
        path('dev/redoc/', dev_schema_view.with_ui('redoc', cache_timeout=0), name='dev-redoc'),
    ]
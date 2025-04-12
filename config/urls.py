"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
  
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from api import views
from config import settings

# Configuración de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Memo Bank API",
        default_version='v1',
        description="Documentación Swagger/OpenAPI para Memo Bank API",
        terms_of_service="https://www.memo-bank.com/terms/",
        contact=openapi.Contact(email="contact@memo-bank.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Definición de urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('api.authentication.urls')),
    
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('app/core/', include('api.core.urls')),
    path('app/accounts/', include('api.accounts.urls')),
    # path('app/transactions/', include('api.transactions.urls')),
    path('app/transfers/', include('api.transfers.urls')),
    path('app/collection/', include('api.collection.urls')),
    path('app/sct/', include('api.sct.urls')),
    path('app/sepa_payment/', include('api.sepa_payment.urls')),
    
    path('', include('api.urls')),
]
 
# Agregar rutas adicionales en modo DEBUG
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""
URL configuration for the Authentication application.

This module defines URL patterns for authentication-related views,
including login, registration, token management, and user profile endpoints.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from api.authentication.views import (
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)


# Authentication API URLs
auth_urlpatterns = [
    # Login and registration
    path('login/', LoginView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    
    # Token management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Password management
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]

# User profile URLs
profile_urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]

# Combined URL patterns
urlpatterns = auth_urlpatterns + profile_urlpatterns
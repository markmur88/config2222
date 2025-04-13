"""
Core views for the API application.

This module defines the main views that are not specific to any particular
app module, including authentication, dashboard, and navigation.
"""
import logging
from typing import Dict, Any, Optional, Union

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View

from rest_framework.response import Response
from rest_framework import status

from api.authentication.serializers import JWTTokenSerializer


# Configure logger
logger = logging.getLogger("api")


class HomeView(View):
    """
    View for the home page.
    
    This view displays the main landing page of the application.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET requests for the home page.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered home page
        """
        return render(request, 'home.html', {'title': _('Welcome')})


class LoginView(View):
    """
    View for user login.
    
    This view handles user authentication and login, supporting both
    session-based authentication and JWT token generation.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the login form.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered login page
        """
        # If user is already logged in, redirect to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
            
        return render(request, 'login.html', {'title': _('Login')})
    
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Handle login form submission.
        
        Args:
            request: The HTTP request with login credentials
            
        Returns:
            HttpResponse: Redirect to dashboard on success or login page with error
        """
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Log login attempt (without password)
        logger.info(f"Login attempt for user: {username}")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Session-based authentication
            login(request, user)
            
            # Generate JWT tokens (but not used in this flow)
            tokens = JWTTokenSerializer.get_tokens_for_user(user)
            
            # Log successful login
            logger.info(f"Successful login for user: {username}")
            
            # Add success message
            messages.success(request, _('Login successful. Welcome back!'))
            
            # Redirect to dashboard
            return redirect('dashboard')
        else:
            # Log failed login
            logger.warning(f"Failed login attempt for user: {username}")
            
            # Add error message
            messages.error(request, _('Invalid credentials. Please try again.'))
            
            # Re-render login page with error
            return render(request, 'login.html', {
                'error': _('Invalid credentials'),
                'username': username,  # Preserve username for convenience
                'title': _('Login')
            })


class LogoutView(View):
    """
    View for user logout.
    
    This view handles user logout and redirects to the home page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle user logout.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: Redirect to home page
        """
        # Log logout if user is authenticated
        if request.user.is_authenticated:
            logger.info(f"Logout for user: {request.user.username}")
            
        # Perform logout
        logout(request)
        
        # Add success message
        messages.success(request, _('You have been logged out successfully.'))
        
        # Redirect to home page
        return redirect('home')


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    """
    View for the main dashboard.
    
    This view displays the main dashboard after successful login.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the dashboard.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered dashboard page
        """
        # Prepare context with user information
        context = {
            'title': _('Dashboard'),
            'user': request.user,
            'username': request.user.username,
            'last_login': request.user.last_login,
        }
        
        return render(request, 'dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class AuthIndexView(View):
    """
    View for the authentication module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the authentication module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/auth/index.html', {
            'title': _('Authentication')
        })


@method_decorator(login_required, name='dispatch')
class CoreIndexView(View):
    """
    View for the core module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the core module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/core/index.html', {
            'title': _('Core')
        })


@method_decorator(login_required, name='dispatch')
class AccountsIndexView(View):
    """
    View for the accounts module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the accounts module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/accounts/index.html', {
            'title': _('Accounts')
        })


@method_decorator(login_required, name='dispatch')
class TransactionsIndexView(View):
    """
    View for the transactions module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the transactions module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/transactions/index.html', {
            'title': _('Transactions')
        })


@method_decorator(login_required, name='dispatch')
class TransfersIndexView(View):
    """
    View for the transfers module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the transfers module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/transfers/index.html', {
            'title': _('Transfers')
        })


@method_decorator(login_required, name='dispatch')
class CollectionIndexView(View):
    """
    View for the collection module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the collection module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/collection/index.html', {
            'title': _('Collections')
        })


@method_decorator(login_required, name='dispatch')
class SCTIndexView(View):
    """
    View for the SEPA Credit Transfer (SCT) module index page.
    """
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Display the SCT module index.
        
        Args:
            request: The HTTP request
            
        Returns:
            HttpResponse: The rendered index page
        """
        return render(request, 'partials/navGeneral/sct/index.html', {
            'title': _('SEPA Credit Transfers')
        })
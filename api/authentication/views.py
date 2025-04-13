"""
Views for user authentication and profile management.
This module defines API views for handling user authentication, registration,
profile management, and password operations.
"""
import logging
from typing import Any, Dict, Optional
from django.contrib.auth import authenticate, get_user_model, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from api.authentication.serializers import (
    JWTTokenSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
    TokenObtainSerializer,
    PasswordResetRequestSerializer  # Added the new serializer import
)

# Configure logger for debugging
logger = logging.getLogger(__name__)
User = get_user_model()

class LoginView(views.APIView):
    """
    API view for user login.
    Handles authentication and returns JWT tokens on successful login.
    """
    permission_classes = [AllowAny]  # Allow access without authentication
    
    @swagger_auto_schema(
        operation_description="User login",
        request_body=TokenObtainSerializer,
        responses={
            200: JWTTokenSerializer,
            400: "Bad request",
            401: "Invalid credentials"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Authenticate user and return JWT tokens.
        
        Args:
            request: The HTTP request containing login credentials
            
        Returns:
            Response: JWT tokens on success or error message
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Validate required fields
        if not username or not password:
            logger.warning("Missing credentials in login request.")
            return Response(
                {'error': _('Username and password are required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if user:
            # Generate tokens
            tokens = JWTTokenSerializer.get_tokens_for_user(user)
            # Add user data to response
            user_data = UserSerializer(user).data
            tokens['user'] = user_data
            logger.info(f"Successful login for user: {username}")
            return Response(tokens, status=status.HTTP_200_OK)
            
        logger.warning(f"Invalid credentials for user: {username}")
        return Response(
            {'error': _('Invalid credentials')},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(views.APIView):
    """
    API view for user logout.
    Handles blacklisting the refresh token to prevent further use.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="User logout",
        responses={
            200: "Successfully logged out",
            400: "Bad request"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Log out a user by blacklisting their refresh token.
        
        Args:
            request: The HTTP request containing the refresh token
            
        Returns:
            Response: Success message or error
        """
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': _('Refresh token is required')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Logout the user from the session
            logout(request)
            logger.info(f"User {request.user.username} logged out successfully")
            return Response(
                {'detail': _('Successfully logged out')},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return Response(
                {'error': _('Invalid token or server error')},
                status=status.HTTP_400_BAD_REQUEST
            )

class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.
    Handles creating new user accounts and returning JWT tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer
    
    @swagger_auto_schema(
        operation_description="Register a new user",
        responses={
            201: JWTTokenSerializer,
            400: "Bad request"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Register a new user and return JWT tokens.
        
        Args:
            request: The HTTP request containing user registration data
            
        Returns:
            Response: JWT tokens on success or validation errors
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens for the new user
            tokens = JWTTokenSerializer.get_tokens_for_user(user)
            # Add user data to response
            user_data = UserSerializer(user).data
            tokens['user'] = user_data
            logger.info(f"User {user.username} registered successfully")
            return Response(tokens, status=status.HTTP_201_CREATED)
            
        logger.warning(f"Registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(views.APIView):
    """
    API view for user profile management.
    Handles retrieving and updating user profile information.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user profile",
        responses={
            200: UserSerializer
        }
    )
    def get(self, request: Request) -> Response:
        """
        Get the authenticated user's profile.
        
        Args:
            request: The HTTP request
            
        Returns:
            Response: User profile data
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    @swagger_auto_schema(
        operation_description="Update user profile",
        request_body=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: "Bad request"
        }
    )
    def put(self, request: Request) -> Response:
        """
        Update the authenticated user's profile.
        
        Args:
            request: The HTTP request containing updated profile data
            
        Returns:
            Response: Updated user profile or validation errors
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return updated user data
            user_data = UserSerializer(request.user).data
            logger.info(f"User {request.user.username} profile updated")
            return Response(user_data, status=status.HTTP_200_OK)
            
        logger.warning(f"Profile update failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(views.APIView):
    """
    API view for changing user password.
    Handles validating current password and setting a new password.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change user password",
        request_body=PasswordChangeSerializer,
        responses={
            200: "Password changed successfully",
            400: "Bad request"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Change the authenticated user's password.
        
        Args:
            request: The HTTP request containing password data
            
        Returns:
            Response: Success message or validation errors
        """
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            # Verify current password
            current_password = serializer.validated_data.get('current_password')
            if not request.user.check_password(current_password):
                return Response(
                    {'current_password': _('Current password is incorrect')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            request.user.set_password(serializer.validated_data.get('new_password'))
            request.user.save()
            logger.info(f"Password changed for user {request.user.username}")
            return Response(
                {'detail': _('Password changed successfully')},
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(views.APIView):
    """
    API view for requesting a password reset.
    Handles generating a password reset token and sending it to the user's email.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Request password reset",
        request_body=PasswordResetRequestSerializer,  # Updated to use the proper serializer
        responses={
            200: "Password reset link sent",
            400: "Bad request",
            404: "User not found"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Request a password reset for the given email.
        
        Args:
            request: The HTTP request containing the user's email
            
        Returns:
            Response: Success message (always return 200 for security)
        """
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': _('Email is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Always return success for security, even if user doesn't exist
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = default_token_generator.make_token(user)
            # In a real implementation, send an email with a reset link
            # For now, just log it
            logger.info(f"Password reset requested for {email}. Token: {token}")
        except User.DoesNotExist:
            # Log but don't expose to client
            logger.warning(f"Password reset requested for non-existent email: {email}")
            
        return Response(
            {'detail': _('If your email is registered, you will receive a password reset link')},
            status=status.HTTP_200_OK
        )

class PasswordResetConfirmView(views.APIView):
    """
    API view for confirming a password reset.
    Handles validating the reset token and setting a new password.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Confirm password reset",
        responses={
            200: "Password reset successful",
            400: "Bad request"
        }
    )
    def post(self, request: Request) -> Response:
        """
        Reset a user's password using a valid token.
        
        Args:
            request: The HTTP request containing the token and new password
            
        Returns:
            Response: Success message or error
        """
        user_id = request.data.get('user_id')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([user_id, token, new_password]):
            return Response(
                {'error': _('User ID, token, and new password are required')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(pk=user_id)
            # Validate token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': _('Invalid or expired token')},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Set new password
            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset successful for user {user.username}")
            return Response(
                {'detail': _('Password reset successful')},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': _('User not found')},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}", exc_info=True)
            return Response(
                {'error': _('Error resetting password')},
                status=status.HTTP_400_BAD_REQUEST
            )

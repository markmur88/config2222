"""
Serializers for user authentication and token management.
This module defines serializers for handling user data and authentication tokens
in API requests and responses.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from typing import Dict, Any

User = get_user_model()  # This will get the CustomUser model we defined

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data.
    Handles conversion between User model instances and API representations.
    """
    class Meta:
        """
        Metadata for the UserSerializer.
        """
        model = User
        fields = ('id', 'username', 'email', 'phone', 'is_active')
        read_only_fields = ('id', 'is_active')

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    Includes password field with write-only access.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        """
        Metadata for the UserCreateSerializer.
        """
        model = User
        fields = ('id', 'username', 'email', 'phone', 'password', 'password_confirm')
        read_only_fields = ('id',)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the passwords match.
        
        Args:
            data: The data to validate
        
        Returns:
            Dict[str, Any]: The validated data
        
        Raises:
            serializers.ValidationError: If passwords don't match
        """
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords don't match."})
        return data
    
    def create(self, validated_data: Dict[str, Any]) -> User:
        """
        Create and save a new user instance.
        
        Args:
            validated_data: The validated data
        
        Returns:
            User: The created user instance
        """
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', '')
        )
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing users.
    Doesn't include password field as that should be handled separately.
    """
    class Meta:
        """
        Metadata for the UserUpdateSerializer.
        """
        model = User
        fields = ('username', 'email', 'phone')

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.
    """
    current_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the new passwords match and the current password is correct.
        
        Args:
            data: The data to validate
        
        Returns:
            Dict[str, Any]: The validated data
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "New passwords don't match."})
        # Current password validation happens in the view
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    
    Only requires an email field to identify the user account.
    """
    email = serializers.EmailField(required=True)

class JWTTokenSerializer(serializers.Serializer):
    """
    Serializer for JWT tokens.
    Used for returning token data in authentication responses.
    """
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer(read_only=True)
    
    @staticmethod
    def get_tokens_for_user(user: User) -> Dict[str, str]:
        """
        Generate JWT tokens for a user.
        
        Args:
            user: The user for whom to generate tokens
        
        Returns:
            Dict[str, str]: Dictionary containing access and refresh tokens
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

class TokenObtainSerializer(serializers.Serializer):
    """
    Serializer for obtaining tokens with username and password.
    """
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
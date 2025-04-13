"""
Admin configuration for the Authentication application.

This module defines the admin interface for authentication-related models,
including custom user management.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from api.authentication.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the CustomUser model.
    
    Extends the default UserAdmin with additional fields and customizations
    specific to the CustomUser model.
    """
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make username readonly when editing an existing user.
        
        Args:
            request: The current request
            obj: The object being edited, or None for a new object
            
        Returns:
            list: List of readonly field names
        """
        if obj:
            return self.readonly_fields + ('username',)
        return self.readonly_fields
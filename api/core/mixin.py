"""
Mixins for the Core application.

This module defines reusable model mixins that can be applied
to Django models across the application to add common functionality.
"""
from typing import Any, List, Optional, Type, Union
from django.db import models
from django.db.models.fields import Field


class UppercaseCharFieldMixin(models.Model):
    """
    Model mixin to automatically convert CharField values to uppercase.
    
    This mixin can be applied to any model to ensure that all CharField
    values are stored in uppercase, which helps maintain data consistency.
    """
    
    class Meta:
        """
        Metadata for the UppercaseCharFieldMixin.
        
        The abstract = True setting ensures this model isn't created in the database.
        """
        abstract = True
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the save method to convert CharField values to uppercase.
        
        This method is called when the model is saved and will:
        1. Find all CharField fields in the model
        2. Convert their values to uppercase (if they are strings)
        3. Call the parent class's save method
        
        Args:
            *args: Variable length argument list to pass to parent's save
            **kwargs: Arbitrary keyword arguments to pass to parent's save
        """
        # Process each field in the model
        for field in self._meta.fields:
            if isinstance(field, models.CharField) and not field.choices:
                value = getattr(self, field.name, None)
                if value and isinstance(value, str):
                    setattr(self, field.name, value.upper())
        
        # Call the parent class's save method
        super().save(*args, **kwargs)


class TimestampMixin(models.Model):
    """
    Model mixin to add created and updated timestamps.
    
    This mixin adds created_at and updated_at fields to any model
    to track when records were created and last modified.
    """
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    
    class Meta:
        """
        Metadata for the TimestampMixin.
        """
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Model mixin to implement soft delete functionality.
    
    Instead of actually deleting records from the database, this mixin
    marks them as deleted by setting a flag, allowing them to be filtered
    out of normal queries while still preserving the data.
    """
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        """
        Metadata for the SoftDeleteMixin.
        """
        abstract = True
    
    def delete(self, *args: Any, **kwargs: Any) -> tuple:
        """
        Override the delete method to implement soft delete.
        
        This method sets the is_deleted flag to True and updates
        the deleted_at timestamp instead of actually deleting the record.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            tuple: A tuple of (number_of_objects_deleted, dict_of_deleted_objects)
        """
        from django.utils import timezone
        
        # Mark as deleted instead of actual deletion
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
        
        # Return a tuple as expected by Django's delete method
        return (1, {self._meta.label: 1})
    
    def hard_delete(self, *args: Any, **kwargs: Any) -> tuple:
        """
        Perform an actual deletion from the database.
        
        This method can be called when a record should actually be
        removed from the database rather than just marked as deleted.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            tuple: Result of the actual delete operation
        """
        return super().delete(*args, **kwargs)


class AuditableMixin(models.Model):
    """
    Model mixin to track who created and last modified a record.
    
    This mixin adds created_by and updated_by fields to any model
    to track which users created and last modified records.
    """
    
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        editable=False
    )
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated',
        editable=False
    )
    
    class Meta:
        """
        Metadata for the AuditableMixin.
        """
        abstract = True
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the save method to track who created/updated the record.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        from api.core.middleware import get_current_user
        
        # Get the current user from middleware
        current_user = get_current_user()
        
        # If this is a new record (no primary key yet)
        if not self.pk and current_user and not self.created_by:
            self.created_by = current_user
        
        # Always update the updated_by field
        if current_user:
            self.updated_by = current_user
        
        # Call the parent class's save method
        super().save(*args, **kwargs)
"""
Database models for user authentication.
This module defines custom user models and managers for the authentication system,
extending Django's built-in user models with additional fields and functionality.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    Provides methods for creating regular users and superusers with appropriate validation.
    """
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and save a regular user.
        
        Args:
            email: The user's email address
            username: The user's username
            password: The user's password
            **extra_fields: Additional fields to set on the user
            
        Returns:
            CustomUser: The created user instance
            
        Raises:
            ValueError: If email or username is not provided
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
        
    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Create and save a superuser.
        
        Args:
            email: The superuser's email address
            username: The superuser's username
            password: The superuser's password
            **extra_fields: Additional fields to set on the user
            
        Returns:
            CustomUser: The created superuser instance
            
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email and username fields.
    Extends Django's authentication model with additional fields and
    custom permission handling.
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Must be a valid email address.'),
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True,
        null=True,
        help_text=_('Optional. Contact phone number.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    
    # Custom related_names to avoid clashes with auth.User
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        related_name='custom_user_set',
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        related_name='custom_user_set',
        help_text=_('Specific permissions for this user.'),
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        """
        Metadata for the CustomUser model.
        """
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['username']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self) -> str:
        """
        String representation of the user.
        
        Returns:
            str: The user's username
        """
        return self.username
    
    def get_full_name(self) -> str:
        """
        Return the user's full name or username if no name is set.
        
        Returns:
            str: The user's full name or username
        """
        return self.username
    
    def get_short_name(self) -> str:
        """
        Return the user's short name or username.
        
        Returns:
            str: The user's short name or username
        """
        return self.username
    
    def email_user(self, subject, message, from_email=None, **kwargs) -> None:
        """
        Send an email to this user.
        
        Args:
            subject: The email subject
            message: The email body
            from_email: The sender's email (optional)
            **kwargs: Additional arguments to pass to the email sending function
        """
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email], **kwargs)
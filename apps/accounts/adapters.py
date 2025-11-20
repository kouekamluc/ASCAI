"""
Custom adapter for django-allauth social account handling.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle Google OAuth signup and account linking."""
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).
        """
        # If this is a social account being connected to an existing user
        if sociallogin.is_existing:
            return
        
        # Check if a user with this email already exists
        email = sociallogin.account.extra_data.get("email", "").lower()
        if email:
            try:
                user = User.objects.get(email=email)
                # User exists, link the social account
                sociallogin.connect(request, user)
                messages.success(
                    request,
                    _("Your Google account has been successfully linked to your existing account.")
                )
            except User.DoesNotExist:
                # New user, proceed with normal signup
                pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social account data.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract name from Google account
        if not user.first_name and data.get("given_name"):
            user.first_name = data.get("given_name", "")
        if not user.last_name and data.get("family_name"):
            user.last_name = data.get("family_name", "")
        
        # Google emails are verified, so activate account immediately
        user.is_active = True
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user after social login.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Log the social login
        import logging
        logger = logging.getLogger("security")
        logger.info(
            f"Social login successful: {user.email} via Google from IP {request.META.get('REMOTE_ADDR')}"
        )
        
        return user


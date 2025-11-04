"""
Permission mixins for forums app.
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import UserBan


class ModeratorRequiredMixin:
    """Mixin to require moderator permissions."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a moderator."""
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to perform this action."))
            return redirect("accounts:login")
        
        if not (request.user.is_admin() or request.user.is_board_member()):
            messages.error(request, _("You do not have permission to perform this action."))
            return redirect("forums:category_list")
        
        return super().dispatch(request, *args, **kwargs)


class MemberRequiredMixin:
    """Mixin to require member permissions."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is a member."""
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to perform this action."))
            return redirect("accounts:login")
        
        if not request.user.is_member():
            messages.error(request, _("You must be a member to perform this action."))
            return redirect("forums:category_list")
        
        return super().dispatch(request, *args, **kwargs)


class NotBannedMixin:
    """Mixin to prevent banned users from posting."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is banned."""
        if request.user.is_authenticated:
            active_ban = UserBan.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if active_ban and active_ban.is_currently_active():
                messages.error(
                    request,
                    _("You are banned from posting. Reason: %(reason)s") % {"reason": active_ban.reason}
                )
                return redirect("forums:category_list")
        
        return super().dispatch(request, *args, **kwargs)


class AuthorOrModeratorRequiredMixin:
    """Mixin to require user to be the author or a moderator."""
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user is author or moderator."""
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to perform this action."))
            return redirect("accounts:login")
        
        obj = self.get_object()
        
        # Check if user is the author or a moderator
        if obj.author != request.user and not (request.user.is_admin() or request.user.is_board_member()):
            messages.error(request, _("You do not have permission to perform this action."))
            return redirect(obj.get_absolute_url())
        
        return super().dispatch(request, *args, **kwargs)







"""
Authentication views for ASCAI platform.
"""

import logging
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from .forms import (
    UserRegistrationForm,
    CustomAuthenticationForm,
    CustomPasswordChangeForm,
    UserUpdateForm,
)
from .models import User, FailedLoginAttempt

logger = logging.getLogger("security")


@require_http_methods(["GET", "POST"])
@csrf_protect
@ratelimit(key="ip", rate="3/h", method="POST", block=True)
def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require email verification
            user.verification_token_created_at = timezone.now()
            user.save()

            logger.info(f"User registration initiated: {user.email} from IP {request.META.get('REMOTE_ADDR')}")

            # Send verification email
            _send_verification_email(request, user)

            return render(
                request,
                "accounts/registration_success.html",
                {"email": user.email},
            )
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
@csrf_protect
@ratelimit(key="ip", rate="5/15m", method="POST", block=True)
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    ip_address = request.META.get("REMOTE_ADDR", "")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    if request.method == "POST":
        email = request.POST.get("username", "").lower()
        
        # Check if account or IP is locked
        if FailedLoginAttempt.is_email_locked(email):
            logger.warning(
                f"Blocked login attempt - account locked: {email} from IP {ip_address}"
            )
            from django.contrib import messages
            messages.error(
                request,
                _(
                    "Account temporarily locked due to too many failed login attempts. "
                    "Please try again in 15 minutes."
                ),
            )
            return render(request, "accounts/login.html", {"form": CustomAuthenticationForm()})

        if FailedLoginAttempt.is_ip_locked(ip_address):
            logger.warning(
                f"Blocked login attempt - IP locked: {email} from IP {ip_address}"
            )
            from django.contrib import messages
            messages.error(
                request,
                _(
                    "IP address temporarily locked due to too many failed login attempts. "
                    "Please try again in 1 hour."
                ),
            )
            return render(request, "accounts/login.html", {"form": CustomAuthenticationForm()})

        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Clear failed attempts for this email on successful login
            FailedLoginAttempt.clear_attempts_for_email(email)
            logger.info(f"Successful login: {user.email} from IP {ip_address}")
            next_url = request.GET.get("next", "dashboard:home")
            return redirect(next_url)
        else:
            # Record failed attempt
            FailedLoginAttempt.record_failed_attempt(email, ip_address, user_agent)
            logger.warning(f"Failed login attempt for email: {email} from IP {ip_address}")
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, _("You have been successfully logged out."))
    return redirect("/")


def _send_verification_email(request, user):
    """Helper function to send verification email."""
    current_site = get_current_site(request)
    mail_subject = _("Activate your ASCAI account")
    message = render_to_string(
        "accounts/activation_email.html",
        {
            "user": user,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )
    send_mail(
        mail_subject,
        message,
        None,
        [user.email],
        fail_silently=False,
    )


@require_http_methods(["GET"])
@ratelimit(key="ip", rate="10/h", method="GET", block=True)
def activate_account(request, uidb64, token):
    """Activate user account via email link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Check token expiration (24 hours)
        if user.verification_token_created_at:
            token_age = timezone.now() - user.verification_token_created_at
            if token_age.total_seconds() > 24 * 3600:  # 24 hours
                logger.warning(
                    f"Expired activation token for {user.email} from IP {request.META.get('REMOTE_ADDR')}"
                )
                messages.error(
                    request,
                    _(
                        "This activation link has expired. Please request a new verification email."
                    ),
                )
                return render(request, "accounts/activation_invalid.html")

        user.is_active = True
        user.verification_token_created_at = None  # Clear token timestamp
        user.save()
        login(request, user)
        logger.info(f"Account activated: {user.email} from IP {request.META.get('REMOTE_ADDR')}")
        return render(request, "accounts/activation_success.html")
    else:
        logger.warning(f"Invalid activation token attempt from IP {request.META.get('REMOTE_ADDR')}")
        return render(request, "accounts/activation_invalid.html")


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="3/h", method="POST", block=True)
def resend_verification_email(request):
    """Resend verification email for inactive accounts."""
    if request.user.is_authenticated and request.user.is_active:
        return redirect("dashboard:home")

    if request.method == "POST":
        email = request.POST.get("email", "").lower()
        try:
            user = User.objects.get(email=email, is_active=False)
            # Update token timestamp
            user.verification_token_created_at = timezone.now()
            user.save()
            _send_verification_email(request, user)
            logger.info(f"Verification email resent to {user.email} from IP {request.META.get('REMOTE_ADDR')}")
            messages.success(
                request,
                _("Verification email has been sent. Please check your inbox."),
            )
            return redirect("accounts:login")
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security)
            messages.success(
                request,
                _("If an account exists with this email, a verification email has been sent."),
            )
            return redirect("accounts:login")

    return render(request, "accounts/resend_verification.html")


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """User profile view."""
    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    """Change password view."""
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Logout and redirect to login with success message
            logout(request)
            return redirect("accounts:login")
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})

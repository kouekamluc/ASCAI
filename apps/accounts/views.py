"""
Authentication views for ASCAI platform.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from .forms import (
    UserRegistrationForm,
    CustomAuthenticationForm,
    CustomPasswordChangeForm,
    UserUpdateForm,
)
from .models import User


@require_http_methods(["GET", "POST"])
@csrf_protect
def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Require email verification
            user.save()

            # Send verification email
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
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "dashboard:home")
            return redirect(next_url)
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """User logout view."""
    logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET"])
def activate_account(request, uidb64, token):
    """Activate user account via email link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, "accounts/activation_success.html")
    else:
        return render(request, "accounts/activation_invalid.html")


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

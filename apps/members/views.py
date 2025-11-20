"""
Member management views for ASCAI platform.
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import csv
from apps.accounts.models import User
from .models import Member, MemberApplication, MemberBadge, MemberAchievement
from .forms import (
    MemberProfileForm,
    MemberAdminForm,
    MemberApplicationForm,
    MemberApplicationReviewForm,
    BulkEmailForm,
)
from .badge_utils import award_badge, check_and_award_badges
from .payment_utils import create_membership_payment, complete_membership_payment, MEMBERSHIP_FEE
from .payment_forms import MembershipPaymentForm, ManualPaymentConfirmationForm
from apps.dashboard.models import Payment
from django.utils import timezone


@login_required
def member_directory(request):
    """Member directory view with search and filter."""
    members = Member.objects.select_related("user").all()
    
    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(membership_number__icontains=search_query) |
            Q(university__icontains=search_query) |
            Q(course__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        members = members.filter(status=status_filter)
    
    # Filter by category
    category_filter = request.GET.get("category", "")
    if category_filter:
        members = members.filter(category=category_filter)
    
    # Filter by university
    university_filter = request.GET.get("university", "")
    if university_filter:
        members = members.filter(university__icontains=university_filter)
    
    # Filter by verification status
    verified_filter = request.GET.get("verified", "")
    if verified_filter == "true":
        members = members.filter(is_verified=True)
    elif verified_filter == "false":
        members = members.filter(is_verified=False)
    
    # Sorting
    sort_by = request.GET.get("sort", "joined_date")
    if sort_by == "name":
        members = members.order_by("user__first_name", "user__last_name")
    elif sort_by == "university":
        members = members.order_by("university", "user__first_name")
    elif sort_by == "joined_date":
        members = members.order_by("-joined_date")
    else:
        members = members.order_by("-joined_date")
    
    # Only show active members to non-admin/board users
    if not (request.user.is_admin() or request.user.is_board_member()):
        members = members.filter(status=Member.MembershipStatus.ACTIVE)
        members = members.filter(profile_public=True)
    
    # Caching for member list (5 minutes)
    from django.core.cache import cache
    cache_key = f'member_list_{request.GET.urlencode()}_{request.user.id if request.user.is_authenticated else "anon"}'
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        # Pagination
        paginator = Paginator(members, 25)  # Increased to 25 per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        # Cache the page object (serialize key data only)
        cache.set(cache_key, {
            'page_number': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }, 300)  # 5 minutes
    else:
        # Recreate paginator for cached page
        paginator = Paginator(members, 25)
        page_number = request.GET.get("page", cached_result.get('page_number', 1))
        page_obj = paginator.get_page(page_number)
    
    # Get badges for members (for display) - only if there are members
    member_badges_dict = {}
    if page_obj and len(page_obj) > 0:
        member_ids = [m.id for m in page_obj]
        if member_ids:
            achievements = MemberAchievement.objects.filter(member_id__in=member_ids).select_related("badge")
            for achievement in achievements:
                if achievement.member_id not in member_badges_dict:
                    member_badges_dict[achievement.member_id] = []
                member_badges_dict[achievement.member_id].append(achievement.badge)
        
        # Attach badges to members for easy template access (always set, even if empty)
        for member in page_obj:
            member.display_badges = member_badges_dict.get(member.id, [])
    
    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "university_filter": university_filter,
        "verified_filter": verified_filter,
        "sort_by": sort_by,
        "status_choices": Member.MembershipStatus.choices,
        "category_choices": Member.MemberCategory.choices,
        "universities": Member.objects.values_list("university", flat=True).distinct().exclude(university=""),
    }
    
    return render(request, "members/directory.html", context)


@login_required
def member_profile(request, user_id):
    """Individual member profile view."""
    user = get_object_or_404(User, id=user_id)
    
    # Check if member exists
    if not hasattr(user, "member_profile"):
        messages.error(request, _("Member profile not found."))
        return redirect("members:directory")
    
    member = user.member_profile
    
    # Privacy check
    if not (request.user.is_admin() or request.user.is_board_member() or request.user == user):
        if not member.profile_public:
            messages.error(request, _("This profile is private."))
            return redirect("members:directory")
    
    # Get member achievements/badges
    achievements = MemberAchievement.objects.filter(member=member).select_related("badge").order_by("-earned_date")
    badges = [achievement.badge for achievement in achievements]
    
    # Get available badges for admin/board (for awarding)
    available_badges = None
    if request.user.is_admin() or request.user.is_board_member():
        earned_badge_ids = [b.id for b in badges]
        available_badges = MemberBadge.objects.exclude(id__in=earned_badge_ids).order_by("name")
    
    context = {
        "member": member,
        "user": user,
        "can_edit": request.user.is_admin() or request.user.is_board_member() or request.user == user,
        "badges": badges,
        "achievements": achievements,
        "available_badges": available_badges,
        "is_admin_or_board": request.user.is_admin() or request.user.is_board_member(),
    }
    
    return render(request, "members/profile.html", context)


@login_required
def export_members_csv(request):
    """Export member data to CSV."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="members_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        _("Membership Number"),
        _("Name"),
        _("Email"),
        _("Status"),
        _("Category"),
        _("University"),
        _("Course"),
        _("Year of Study"),
        _("City"),
        _("Country"),
        _("Joined Date"),
    ])
    
    members = Member.objects.select_related("user").all()
    for member in members:
        writer.writerow([
            member.membership_number or "",
            member.user.full_name,
            member.user.email if member.email_public or request.user.is_admin() else "",
            member.get_status_display(),
            member.get_category_display(),
            member.university,
            member.course,
            member.year_of_study or "",
            member.city,
            member.country_of_origin,
            member.joined_date.strftime("%Y-%m-%d") if member.joined_date else "",
        ])
    
    return response


@login_required
@require_http_methods(["POST"])
def bulk_update_status(request):
    """Bulk update member status."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    member_ids = request.POST.getlist("member_ids")
    new_status = request.POST.get("new_status")
    
    if member_ids and new_status:
        Member.objects.filter(id__in=member_ids).update(status=new_status)
        messages.success(request, _("Member status updated successfully."))
    else:
        messages.error(request, _("Invalid request."))
    
    return redirect("members:directory")


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request, user_id=None):
    """Edit member profile view."""
    # If no user_id provided, edit own profile
    if user_id is None:
        user_id = request.user.id
    
    user = get_object_or_404(User, id=user_id)
    
    # Check if member profile exists
    if not hasattr(user, "member_profile"):
        messages.error(request, _("Member profile not found."))
        return redirect("members:directory")
    
    member = user.member_profile
    
    # Permission check: user can edit own profile, admin/board can edit any
    is_admin_or_board = request.user.is_admin() or request.user.is_board_member()
    can_edit = is_admin_or_board or request.user == user
    
    if not can_edit:
        messages.error(request, _("You don't have permission to edit this profile."))
        return redirect("members:profile", user_id=user.id)
    
    if request.method == "POST":
        # Use appropriate form based on permissions
        if is_admin_or_board:
            profile_form = MemberProfileForm(request.POST, instance=member)
            admin_form = MemberAdminForm(request.POST, instance=member)
            
            if profile_form.is_valid() and admin_form.is_valid():
                profile_form.save()
                admin_form.save()
                messages.success(request, _("Profile updated successfully."))
                return redirect("members:profile", user_id=user.id)
        else:
            profile_form = MemberProfileForm(request.POST, instance=member)
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, _("Profile updated successfully."))
                return redirect("members:profile", user_id=user.id)
    else:
        # GET request - initialize forms
        if is_admin_or_board:
            profile_form = MemberProfileForm(instance=member)
            admin_form = MemberAdminForm(instance=member)
        else:
            profile_form = MemberProfileForm(instance=member)
            admin_form = None
    
    context = {
        "member": member,
        "user": user,
        "profile_form": profile_form,
        "admin_form": admin_form,
        "is_admin_or_board": is_admin_or_board,
    }
    
    return render(request, "members/edit_profile.html", context)


@require_http_methods(["GET", "POST"])
def apply_for_membership(request):
    """Apply for membership view."""
    # If user is not authenticated, redirect to login with next parameter
    if not request.user.is_authenticated:
        messages.info(request, _("Please log in or register to apply for membership."))
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    
    # Check if user already has a member profile
    if hasattr(request.user, "member_profile"):
        messages.info(request, _("You already have a member profile."))
        return redirect("members:profile", user_id=request.user.id)
    
    # Check if user has a pending application
    pending_app = MemberApplication.objects.filter(
        user=request.user, status=MemberApplication.ApplicationStatus.PENDING
    ).first()
    
    if pending_app:
        messages.info(request, _("You already have a pending application."))
        return redirect("members:application_status")
    
    if request.method == "POST":
        form = MemberApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = MemberApplication.ApplicationStatus.PENDING
            application.save()
            messages.success(
                request,
                _(
                    "Your membership application has been submitted. We'll review it shortly."
                ),
            )
            return redirect("members:application_status")
    else:
        form = MemberApplicationForm()
    
    return render(request, "members/apply.html", {"form": form})


@login_required
def view_application_status(request):
    """View application status for current user."""
    applications = MemberApplication.objects.filter(user=request.user).order_by(
        "-application_date"
    )
    latest_application = applications.first() if applications.exists() else None
    
    context = {
        "applications": applications,
        "latest_application": latest_application,
    }
    
    return render(request, "members/application_status.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def review_application(request, application_id):
    """Review member application (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    application = get_object_or_404(MemberApplication, id=application_id)
    
    if request.method == "POST":
        form = MemberApplicationReviewForm(request.POST, instance=application)
        action = request.POST.get("action")
        
        if form.is_valid():
            if action == "approve":
                application.approve(request.user)
                form.save()
                messages.success(
                    request,
                    _("Application approved. Member profile created."),
                )
            elif action == "reject":
                application.reject(request.user, form.cleaned_data.get("review_notes", ""))
                form.save()
                messages.success(request, _("Application rejected."))
            else:
                form.save()
                messages.success(request, _("Application updated."))
            
            return redirect("members:application_list")
    else:
        form = MemberApplicationReviewForm(instance=application)
    
    context = {
        "application": application,
        "form": form,
    }
    
    return render(request, "members/review_application.html", context)


@login_required
def application_list(request):
    """List all applications (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    applications = MemberApplication.objects.select_related("user", "reviewed_by").prefetch_related("user__profile").all()
    
    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "status_choices": MemberApplication.ApplicationStatus.choices,
    }
    
    return render(request, "members/application_list.html", context)


@login_required
@require_http_methods(["POST"])
def verify_member(request, member_id):
    """Verify or unverify a member (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    member = get_object_or_404(Member, id=member_id)
    action = request.POST.get("action")
    
    if action == "verify":
        member.is_verified = True
        member.verified_at = timezone.now()
        member.verified_by = request.user
        member.save()
        messages.success(request, _("Member verified successfully."))
    elif action == "unverify":
        member.is_verified = False
        member.verified_at = None
        member.verified_by = None
        member.save()
        messages.success(request, _("Member verification removed."))
    else:
        messages.error(request, _("Invalid action."))
    
    # Redirect back to where they came from or member profile
    redirect_url = request.POST.get("next", "members:profile")
    if redirect_url == "members:profile":
        return redirect(redirect_url, user_id=member.user.id)
    return redirect(redirect_url)


@login_required
@require_http_methods(["POST"])
def award_badge_to_member(request, member_id):
    """Award a badge to a member (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    member = get_object_or_404(Member, id=member_id)
    badge_id = request.POST.get("badge_id")
    notes = request.POST.get("notes", "")
    
    if badge_id:
        badge = get_object_or_404(MemberBadge, id=badge_id)
        if award_badge(member, badge, notes):
            messages.success(request, _("Badge awarded successfully."))
        else:
            messages.info(request, _("Member already has this badge."))
    else:
        messages.error(request, _("Invalid badge."))
    
    return redirect("members:profile", user_id=member.user.id)


@login_required
@require_http_methods(["POST"])
def remove_badge_from_member(request, achievement_id):
    """Remove a badge from a member (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    achievement = get_object_or_404(MemberAchievement, id=achievement_id)
    member = achievement.member
    achievement.delete()
    messages.success(request, _("Badge removed successfully."))
    
    return redirect("members:profile", user_id=member.user.id)


@login_required
@require_http_methods(["GET", "POST"])
def pay_membership(request):
    """Initiate membership payment."""
    # Check if user already has active membership
    if hasattr(request.user, "member_profile"):
        member = request.user.member_profile
        if member.status == Member.MembershipStatus.ACTIVE:
            # Check if there's a completed payment
            completed_payment = Payment.objects.filter(
                user=request.user,
                payment_type=Payment.PaymentType.MEMBERSHIP,
                status=Payment.PaymentStatus.COMPLETED,
            ).first()
            
            if completed_payment:
                messages.info(request, _("You already have an active membership."))
                return redirect("members:profile", user_id=request.user.id)
    
    # Check for existing pending payment
    pending_payment = Payment.objects.filter(
        user=request.user,
        payment_type=Payment.PaymentType.MEMBERSHIP,
        status=Payment.PaymentStatus.PENDING,
    ).first()
    
    if request.method == "POST":
        form = MembershipPaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data["payment_method"]
            notes = form.cleaned_data.get("notes", "")
            amount = form.cleaned_data.get("amount", MEMBERSHIP_FEE)
            
            # Create or update payment
            if pending_payment:
                payment = pending_payment
                payment.payment_method = payment_method
                payment.notes = notes
                payment.amount = amount
                payment.save()
            else:
                payment = create_membership_payment(
                    request.user,
                    amount=amount,
                    payment_method=payment_method,
                    notes=notes,
                )
            
            # Handle different payment methods
            if payment_method == "manual":
                # For manual payment, show confirmation page
                return redirect("members:payment_confirmation", payment_id=payment.id)
            elif payment_method == "stripe":
                # TODO: Integrate Stripe payment
                messages.info(request, _("Stripe integration coming soon."))
                return redirect("members:payment_status", payment_id=payment.id)
            elif payment_method == "paypal":
                # TODO: Integrate PayPal payment
                messages.info(request, _("PayPal integration coming soon."))
                return redirect("members:payment_status", payment_id=payment.id)
    else:
        form = MembershipPaymentForm()
    
    context = {
        "form": form,
        "membership_fee": MEMBERSHIP_FEE,
        "pending_payment": pending_payment,
    }
    
    return render(request, "members/pay_membership.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def payment_confirmation(request, payment_id):
    """Manual payment confirmation page."""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != Payment.PaymentStatus.PENDING:
        messages.info(request, _("This payment is no longer pending."))
        return redirect("members:payment_status", payment_id=payment.id)
    
    if request.method == "POST":
        form = ManualPaymentConfirmationForm(request.POST)
        if form.is_valid():
            # Update payment with transaction reference
            transaction_ref = form.cleaned_data.get("transaction_reference", "")
            notes = form.cleaned_data.get("notes", "")
            
            if transaction_ref:
                payment.transaction_id = transaction_ref
            if notes:
                payment.notes = f"{payment.notes}\n{notes}".strip() if payment.notes else notes
            
            payment.save()
            messages.success(
                request,
                _(
                    "Payment confirmation submitted. Your membership will be activated once payment is verified by admin."
                ),
            )
            return redirect("members:payment_status", payment_id=payment.id)
    else:
        form = ManualPaymentConfirmationForm()
    
    context = {
        "payment": payment,
        "form": form,
    }
    
    return render(request, "members/payment_confirmation.html", context)


@login_required
def payment_status(request, payment_id):
    """View payment status."""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        "payment": payment,
    }
    
    return render(request, "members/payment_status.html", context)


@login_required
def payment_history(request):
    """View user's payment history."""
    payments = Payment.objects.filter(user=request.user).order_by("-created_at")
    
    context = {
        "payments": payments,
    }
    
    return render(request, "members/payment_history.html", context)


@login_required
@require_http_methods(["POST"])
def approve_payment(request, payment_id):
    """Admin action to approve a payment (mark as completed)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status == Payment.PaymentStatus.COMPLETED:
        messages.info(request, _("Payment is already completed."))
        return redirect("admin:dashboard_payment_change", payment.id)
    
    # Complete the payment
    transaction_id = request.POST.get("transaction_id", payment.transaction_id or "")
    payment_method = request.POST.get("payment_method", payment.payment_method or "Manual")
    
    member = complete_membership_payment(payment, transaction_id, payment_method)
    
    messages.success(
        request,
        _("Payment approved. Member {} has been activated.").format(member.user.full_name),
    )
    
    return redirect("admin:dashboard_payment_change", payment.id)


@login_required
def check_member_badges(request, member_id):
    """Check and auto-award badges for a member (admin/board only)."""
    if not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("Permission denied."))
        return redirect("members:directory")
    
    member = get_object_or_404(Member, id=member_id)
    awards = check_and_award_badges(member)
    
    if awards:
        messages.success(
            request,
            _("Awarded {} badge(s): {}").format(
                len(awards), ", ".join([b.name for b in awards])
            ),
        )
    else:
        messages.info(request, _("No new badges to award."))
    
    return redirect("members:profile", user_id=member.user.id)

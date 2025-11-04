"""
Member management views for ASCAI platform.
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import csv
from apps.accounts.models import User
from .models import Member


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
    
    # Only show active members to non-admin/board users
    if not (request.user.is_admin() or request.user.is_board_member()):
        members = members.filter(status=Member.MembershipStatus.ACTIVE)
        members = members.filter(profile_public=True)
    
    # Pagination
    paginator = Paginator(members, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "university_filter": university_filter,
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
    
    context = {
        "member": member,
        "user": user,
        "can_edit": request.user.is_admin() or request.user.is_board_member() or request.user == user,
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

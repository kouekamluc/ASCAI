"""
Admin configuration for members app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django import forms
from datetime import timedelta
from .models import Member, MemberApplication, MemberBadge, MemberAchievement, MembershipSubscriptionSettings
from .badge_utils import award_badge
from .payment_utils import get_default_subscription_duration_years


class SubscriptionExtensionForm(forms.Form):
    """Form for extending subscription periods."""
    years = forms.IntegerField(
        label=_("Years"),
        min_value=0,
        help_text=_("Number of years to extend"),
    )
    months = forms.IntegerField(
        label=_("Months"),
        min_value=0,
        max_value=11,
        initial=0,
        help_text=_("Additional months to extend"),
    )
    days = forms.IntegerField(
        label=_("Days"),
        min_value=0,
        max_value=30,
        initial=0,
        help_text=_("Additional days to extend"),
    )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member model."""

    list_display = [
        "user",
        "membership_number",
        "status",
        "category",
        "is_verified",
        "university",
        "membership_expiry",
        "subscription_status_display",
        "joined_date",
    ]
    list_filter = [
        "status",
        "category",
        "is_verified",
        "profile_public",
        "joined_date",
        "membership_expiry",
        "country_of_origin",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "membership_number",
        "university",
        "course",
    ]
    readonly_fields = ["created_at", "updated_at", "joined_date", "verified_at"]
    actions = ["verify_members", "unverify_members", "check_and_award_badges", "activate_members", "deactivate_members", "extend_subscriptions"]
    
    fieldsets = (
        (_("User"), {"fields": ("user",)}),
        (
            _("Membership"),
            {
                "fields": (
                    "membership_number",
                    "status",
                    "category",
                    "joined_date",
                    "membership_expiry",
                )
            },
        ),
        (
            _("Academic Information"),
            {
                "fields": (
                    "university",
                    "course",
                    "year_of_study",
                    "graduation_year",
                )
            },
        ),
        (
            _("Personal Information"),
            {
                "fields": (
                    "city",
                    "country_of_origin",
                    "date_of_birth",
                    "linkedin",
                    "website",
                )
            },
        ),
        (
            _("Privacy Settings"),
            {"fields": ("profile_public", "email_public")},
        ),
        (
            _("Verification"),
            {
                "fields": (
                    "is_verified",
                    "verified_at",
                    "verified_by",
                )
            },
        ),
        (_("Metadata"), {"fields": ("created_at", "updated_at")}),
    )
    
    def verify_members(self, request, queryset):
        """Bulk verify selected members."""
        count = queryset.update(
            is_verified=True,
            verified_at=timezone.now(),
            verified_by=request.user,
        )
        self.message_user(request, _("{} members verified successfully.").format(count))
    verify_members.short_description = _("Verify selected members")
    
    def unverify_members(self, request, queryset):
        """Bulk unverify selected members."""
        count = queryset.update(
            is_verified=False,
            verified_at=None,
            verified_by=None,
        )
        self.message_user(request, _("{} members unverified successfully.").format(count))
    unverify_members.short_description = _("Unverify selected members")
    
    def check_and_award_badges(self, request, queryset):
        """Check and award badges to selected members."""
        from .badge_utils import check_and_award_badges
        total_awards = 0
        for member in queryset:
            awards = check_and_award_badges(member)
            total_awards += len(awards)
        self.message_user(
            request,
            _("Checked {} members and awarded {} new badge(s).").format(
                queryset.count(), total_awards
            ),
        )
    check_and_award_badges.short_description = _("Check and award badges to selected members")
    
    def activate_members(self, request, queryset):
        """Activate selected members (set status to active)."""
        count = queryset.update(status=Member.MembershipStatus.ACTIVE)
        self.message_user(request, _("{} member(s) activated successfully.").format(count))
    activate_members.short_description = _("Activate selected members")
    
    def deactivate_members(self, request, queryset):
        """Deactivate selected members (set status to inactive)."""
        count = queryset.update(status=Member.MembershipStatus.INACTIVE)
        self.message_user(request, _("{} member(s) deactivated successfully.").format(count))
    deactivate_members.short_description = _("Deactivate selected members")
    
    def subscription_status_display(self, obj):
        """Display subscription status with color coding."""
        if not obj.membership_expiry:
            return format_html('<span style="color: orange;">⚠️ No expiry set</span>')
        
        if obj.is_subscription_expired():
            days_expired = abs(obj.days_until_expiry() or 0)
            return format_html(
                '<span style="color: red;">❌ Expired ({} days ago)</span>',
                days_expired
            )
        else:
            days_left = obj.days_until_expiry() or 0
            if days_left <= 30:
                return format_html(
                    '<span style="color: orange;">⚠️ Expires in {} days</span>',
                    days_left
                )
            else:
                return format_html(
                    '<span style="color: green;">✓ Active ({} days left)</span>',
                    days_left
                )
    subscription_status_display.short_description = _("Subscription Status")
    
    def extend_subscriptions(self, request, queryset):
        """Extend subscriptions for selected members."""
        # Store selected member IDs in session
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['extend_subscription_ids'] = selected_ids
        return redirect(reverse('admin:members_member_extend_subscription_period'))
    extend_subscriptions.short_description = _("Extend subscription period for selected members")
    
    def get_urls(self):
        """Add custom URLs for subscription extension."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'extend-subscription-period/',
                self.admin_site.admin_view(self.extend_subscription_period_view),
                name='members_member_extend_subscription_period',
            ),
        ]
        return custom_urls + urls
    
    def extend_subscription_period_view(self, request):
        """View for extending subscription periods."""
        from django.contrib.admin.options import IS_POPUP_VAR
        from django.template.response import TemplateResponse
        
        # Get member IDs from session
        member_ids = request.session.get('extend_subscription_ids', [])
        if not member_ids:
            messages.error(request, _("No members selected."))
            return redirect('admin:members_member_changelist')
        
        members = Member.objects.filter(id__in=member_ids)
        
        if request.method == 'POST':
            form = SubscriptionExtensionForm(request.POST)
            if form.is_valid():
                years = form.cleaned_data['years']
                months = form.cleaned_data['months']
                days = form.cleaned_data['days']
                
                # Calculate total days
                total_days = (years * 365) + (months * 30) + days
                
                if total_days <= 0:
                    messages.error(request, _("Please enter a valid extension period."))
                else:
                    updated_count = 0
                    for member in members:
                        # Calculate new expiry date
                        if member.membership_expiry:
                            # Extend from current expiry date
                            new_expiry = member.membership_expiry + timedelta(days=total_days)
                        else:
                            # If no expiry date, extend from today
                            new_expiry = timezone.now().date() + timedelta(days=total_days)
                        
                        member.membership_expiry = new_expiry
                        # Activate member if not already active
                        if member.status != Member.MembershipStatus.ACTIVE:
                            member.status = Member.MembershipStatus.ACTIVE
                        member.save()
                        updated_count += 1
                    
                    messages.success(
                        request,
                        _("Successfully extended subscription for {} member(s).").format(updated_count)
                    )
                    
                    # Clear session
                    if 'extend_subscription_ids' in request.session:
                        del request.session['extend_subscription_ids']
                    
                    return redirect('admin:members_member_changelist')
        else:
            form = SubscriptionExtensionForm(initial={
                'years': get_default_subscription_duration_years(),
                'months': 0,
                'days': 0,
            })
        
        context = {
            'form': form,
            'members': members,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, None),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, None),
            'has_delete_permission': self.has_delete_permission(request, None),
            'has_editable_inline_admin_formsets': False,
            'is_popup': IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET,
        }
        
        return TemplateResponse(
            request,
            'admin/members/extend_subscription.html',
            context,
        )


@admin.register(MemberApplication)
class MemberApplicationAdmin(admin.ModelAdmin):
    """Admin interface for MemberApplication model."""

    list_display = [
        "user",
        "application_date",
        "status",
        "reviewed_by",
        "reviewed_at",
    ]
    list_filter = [
        "status",
        "application_date",
        "reviewed_at",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "notes",
        "review_notes",
    ]
    readonly_fields = ["application_date", "reviewed_at"]
    date_hierarchy = "application_date"
    
    fieldsets = (
        (_("Application"), {"fields": ("user", "application_date", "status", "notes")}),
        (
            _("Review"),
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                    "review_notes",
                )
            },
        ),
    )


@admin.register(MemberBadge)
class MemberBadgeAdmin(admin.ModelAdmin):
    """Admin interface for MemberBadge model."""

    list_display = [
        "name",
        "category",
        "icon",
        "created_at",
    ]
    list_filter = [
        "category",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = ["created_at"]
    
    fieldsets = (
        (_("Badge Information"), {"fields": ("name", "description", "category", "icon")}),
        (_("Metadata"), {"fields": ("created_at",)}),
    )


@admin.register(MemberAchievement)
class MemberAchievementAdmin(admin.ModelAdmin):
    """Admin interface for MemberAchievement model."""

    list_display = [
        "member",
        "badge",
        "earned_date",
    ]
    list_filter = [
        "earned_date",
        "badge__category",
    ]
    search_fields = [
        "member__user__email",
        "member__user__first_name",
        "member__user__last_name",
        "badge__name",
    ]
    readonly_fields = ["earned_date"]
    date_hierarchy = "earned_date"
    
    fieldsets = (
        (_("Achievement"), {"fields": ("member", "badge", "earned_date", "notes")}),
    )


@admin.register(MembershipSubscriptionSettings)
class MembershipSubscriptionSettingsAdmin(admin.ModelAdmin):
    """Admin interface for Membership Subscription Settings."""
    
    def has_add_permission(self, request):
        """Prevent adding new instances - only one allowed."""
        return not MembershipSubscriptionSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton instance."""
        return False
    
    list_display = ["default_subscription_duration_years", "updated_at", "updated_by"]
    readonly_fields = ["updated_at"]
    
    fieldsets = (
        (
            _("Subscription Settings"),
            {
                "fields": (
                    "default_subscription_duration_years",
                    "updated_at",
                    "updated_by",
                ),
                "description": _(
                    "Configure the default subscription duration for membership payments. "
                    "This will be used when members make payments unless overridden."
                ),
            },
        ),
    )
    
    def save_model(self, request, obj, form, change):
        """Save the model and track who updated it."""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Return queryset with only one object."""
        return super().get_queryset(request).filter(pk=1)

"""
Member models for ASCAI platform.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Member(models.Model):
    """Extended member profile linked to User."""

    class MembershipStatus(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        SUSPENDED = "suspended", _("Suspended")
        PENDING = "pending", _("Pending")

    class MemberCategory(models.TextChoices):
        STUDENT = "student", _("Student")
        ALUMNI = "alumni", _("Alumni")
        HONORARY = "honorary", _("Honorary Member")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
    )
    membership_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True
    )
    status = models.CharField(
        max_length=10,
        choices=MembershipStatus.choices,
        default=MembershipStatus.PENDING,
    )
    category = models.CharField(
        max_length=10,
        choices=MemberCategory.choices,
        default=MemberCategory.STUDENT,
    )
    
    # Academic information
    university = models.CharField(_("university"), max_length=200, blank=True)
    course = models.CharField(_("course of study"), max_length=200, blank=True)
    year_of_study = models.IntegerField(_("year of study"), blank=True, null=True)
    graduation_year = models.IntegerField(
        _("graduation year"), blank=True, null=True
    )
    
    # Additional information
    city = models.CharField(_("city"), max_length=100, blank=True)
    country_of_origin = models.CharField(
        _("country of origin"), max_length=100, default="Cameroon"
    )
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)
    
    # Membership dates
    joined_date = models.DateField(_("joined date"), auto_now_add=True)
    membership_expiry = models.DateField(
        _("membership expiry"), blank=True, null=True
    )
    
    # Privacy settings
    profile_public = models.BooleanField(
        _("public profile"), default=True
    )
    email_public = models.BooleanField(
        _("public email"), default=False
    )
    
    # Additional fields
    linkedin = models.URLField(_("LinkedIn"), blank=True)
    website = models.URLField(_("website"), blank=True)
    
    # Verification fields
    is_verified = models.BooleanField(_("is verified"), default=False)
    verified_at = models.DateTimeField(_("verified at"), blank=True, null=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_members",
        blank=True,
        null=True,
        verbose_name=_("verified by"),
    )
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("member")
        verbose_name_plural = _("members")
        ordering = ["-joined_date"]

    def __str__(self):
        return f"{self.user.full_name} ({self.membership_number or 'N/A'})"

    def is_active_member(self):
        """Check if member has active status."""
        return self.status == self.MembershipStatus.ACTIVE
    
    def is_subscription_active(self):
        """Check if member's subscription is currently active (not expired)."""
        if not self.is_active_member():
            return False
        
        if not self.membership_expiry:
            return False
        
        from django.utils import timezone
        return self.membership_expiry > timezone.now().date()
    
    def days_until_expiry(self):
        """Get number of days until membership expires. Returns negative if expired."""
        if not self.membership_expiry:
            return None
        
        from django.utils import timezone
        today = timezone.now().date()
        delta = self.membership_expiry - today
        return delta.days
    
    def is_subscription_expired(self):
        """Check if member's subscription has expired."""
        if not self.membership_expiry:
            return False
        
        from django.utils import timezone
        return self.membership_expiry <= timezone.now().date()


class MemberApplication(models.Model):
    """Member application model for membership requests."""

    class ApplicationStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_applications",
        verbose_name=_("user"),
    )
    application_date = models.DateTimeField(_("application date"), auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        verbose_name=_("status"),
    )
    notes = models.TextField(_("notes"), blank=True, help_text=_("Internal notes about the application"))
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_applications",
        blank=True,
        null=True,
        verbose_name=_("reviewed by"),
    )
    reviewed_at = models.DateTimeField(_("reviewed at"), blank=True, null=True)
    review_notes = models.TextField(_("review notes"), blank=True, help_text=_("Notes from the reviewer"))

    class Meta:
        verbose_name = _("member application")
        verbose_name_plural = _("member applications")
        ordering = ["-application_date"]

    def __str__(self):
        return f"{self.user.full_name} - {self.get_status_display()} ({self.application_date.date()})"

    def approve(self, reviewer):
        """Approve the application and create member profile."""
        from django.utils import timezone
        self.status = self.ApplicationStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
        
        # Create member profile if it doesn't exist
        if not hasattr(self.user, "member_profile"):
            Member.objects.create(
                user=self.user,
                status=Member.MembershipStatus.PENDING,
            )
        
        # Update user role to member
        if self.user.role == self.user.Role.PUBLIC:
            self.user.role = self.user.Role.MEMBER
            self.user.save()

    def reject(self, reviewer, notes=""):
        """Reject the application."""
        from django.utils import timezone
        self.status = self.ApplicationStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()


class MemberBadge(models.Model):
    """Badge model for member achievements."""

    class BadgeCategory(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership")
        ACTIVITY = "activity", _("Activity")
        ACHIEVEMENT = "achievement", _("Achievement")
        SPECIAL = "special", _("Special")

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True)
    icon = models.CharField(
        _("icon"),
        max_length=50,
        blank=True,
        help_text=_("Icon class name (e.g., 'icon-star', 'icon-trophy')"),
    )
    category = models.CharField(
        max_length=20,
        choices=BadgeCategory.choices,
        default=BadgeCategory.ACHIEVEMENT,
        verbose_name=_("category"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("badge")
        verbose_name_plural = _("badges")
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class MemberAchievement(models.Model):
    """Links members to badges they have earned."""

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name=_("member"),
    )
    badge = models.ForeignKey(
        MemberBadge,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name=_("badge"),
    )
    earned_date = models.DateTimeField(_("earned date"), auto_now_add=True)
    notes = models.TextField(_("notes"), blank=True, help_text=_("Optional notes about earning this badge"))

    class Meta:
        verbose_name = _("member achievement")
        verbose_name_plural = _("member achievements")
        ordering = ["-earned_date"]
        unique_together = [["member", "badge"]]

    def __str__(self):
        return f"{self.member.user.full_name} - {self.badge.name}"


class MembershipSubscriptionSettings(models.Model):
    """Singleton model for membership subscription settings."""
    
    default_subscription_duration_years = models.PositiveIntegerField(
        _("default subscription duration (years)"),
        default=2,
        help_text=_("Default number of years for membership subscription when a member pays"),
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_subscription_settings",
        blank=True,
        null=True,
        verbose_name=_("updated by"),
    )
    
    class Meta:
        verbose_name = _("membership subscription settings")
        verbose_name_plural = _("membership subscription settings")
    
    def __str__(self):
        return _("Membership Subscription Settings")
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Get or create the singleton instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

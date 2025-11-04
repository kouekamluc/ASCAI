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

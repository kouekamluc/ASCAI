"""
Dashboard models for ASCAI platform.
Includes Payment models to support analytics.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Payment(models.Model):
    """Payment model for revenue tracking and analytics."""
    
    class PaymentType(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership Fee")
        EVENT = "event", _("Event Registration")
        DONATION = "donation", _("Donation")
        OTHER = "other", _("Other")
    
    class PaymentStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
        REFUNDED = "refunded", _("Refunded")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        related_name="payments",
        blank=True,
        null=True,
        verbose_name=_("member"),
        help_text=_("Member profile linked to this payment"),
    )
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.MEMBERSHIP,
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    transaction_id = models.CharField(
        _("transaction ID"), max_length=100, blank=True
    )
    payment_method = models.CharField(
        _("payment method"),
        max_length=50,
        blank=True,
        help_text=_("e.g., Stripe, PayPal, Bank Transfer, Manual"),
    )
    notes = models.TextField(_("notes"), blank=True, help_text=_("Additional payment notes"))
    paid_at = models.DateTimeField(_("paid at"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.full_name} - €{self.amount} ({self.get_status_display()})"
    
    def clean(self):
        """Validate payment data."""
        if self.payment_type == self.PaymentType.MEMBERSHIP:
            # For membership payments, ensure member is linked
            if not self.member and hasattr(self.user, "member_profile"):
                self.member = self.user.member_profile
    
    def save(self, *args, **kwargs):
        """Override save to auto-link member if needed."""
        if self.payment_type == self.PaymentType.MEMBERSHIP and not self.member:
            if hasattr(self.user, "member_profile"):
                self.member = self.user.member_profile
        super().save(*args, **kwargs)

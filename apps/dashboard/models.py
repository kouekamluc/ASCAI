"""
Dashboard models for ASCAI platform.
Includes Payment models to support analytics.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


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
    paid_at = models.DateTimeField(_("paid at"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.amount} ({self.status})"

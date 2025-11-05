"""
Dashboard admin configuration.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Payment
from apps.members.payment_utils import complete_membership_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    list_display = ("user", "member", "amount", "payment_type", "status", "payment_method", "paid_at", "created_at")
    list_filter = ("payment_type", "status", "payment_method", "created_at", "paid_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "transaction_id", "notes")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "paid_at")
    actions = ["approve_payments", "mark_as_failed"]
    
    fieldsets = (
        (_("Payment Information"), {
            "fields": ("user", "member", "amount", "payment_type", "status", "payment_method")
        }),
        (_("Transaction Details"), {
            "fields": ("transaction_id", "notes", "paid_at", "created_at")
        }),
    )
    
    def approve_payments(self, request, queryset):
        """Approve selected payments (mark as completed)."""
        count = 0
        for payment in queryset:
            if payment.status == Payment.PaymentStatus.PENDING:
                if payment.payment_type == Payment.PaymentType.MEMBERSHIP:
                    try:
                        complete_membership_payment(
                            payment,
                            transaction_id=payment.transaction_id or f"ADMIN-{payment.id}",
                            payment_method=payment.payment_method or "Manual",
                        )
                        count += 1
                    except Exception as e:
                        self.message_user(request, f"Error processing payment {payment.id}: {e}", level="error")
                else:
                    # For non-membership payments, just mark as completed
                    payment.status = Payment.PaymentStatus.COMPLETED
                    payment.paid_at = timezone.now()
                    payment.save()
                    count += 1
        
        self.message_user(request, _("{} payment(s) approved successfully.").format(count))
    approve_payments.short_description = _("Approve selected payments")
    
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed."""
        count = queryset.update(status=Payment.PaymentStatus.FAILED)
        self.message_user(request, _("{} payment(s) marked as failed.").format(count))
    mark_as_failed.short_description = _("Mark selected payments as failed")

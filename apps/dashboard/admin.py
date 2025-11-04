"""
Dashboard admin configuration.
"""

from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    list_display = ("user", "amount", "payment_type", "status", "paid_at", "created_at")
    list_filter = ("payment_type", "status", "created_at", "paid_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "transaction_id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

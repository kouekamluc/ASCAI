"""
Signals for members app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.dashboard.models import Payment
from .payment_utils import complete_membership_payment


@receiver(post_save, sender=Payment)
def handle_payment_completion(sender, instance, created, **kwargs):
    """Handle payment completion and activate member with subscription expiry."""
    # Only process if payment is completed and is a membership payment
    if (
        instance.status == Payment.PaymentStatus.COMPLETED
        and instance.payment_type == Payment.PaymentType.MEMBERSHIP
        and not created  # Only on update, not creation
    ):
        try:
            # Use the payment_utils function which handles expiry dates
            complete_membership_payment(
                instance,
                transaction_id=instance.transaction_id,
                payment_method=instance.payment_method or "Manual",
            )
        except Exception as e:
            # Log error but don't break the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing membership payment completion: {e}")


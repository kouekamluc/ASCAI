"""
Payment utilities for membership payments.
"""

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from apps.dashboard.models import Payment
from apps.accounts.models import User
from .models import MembershipSubscriptionSettings


MEMBERSHIP_FEE = Decimal("10.00")  # 10 EUR


def get_default_subscription_duration_years():
    """Get default subscription duration from admin settings."""
    settings_obj = MembershipSubscriptionSettings.load()
    return settings_obj.default_subscription_duration_years


def create_membership_payment(user, amount=None, payment_method="", notes=""):
    """Create a membership payment for a user."""
    if amount is None:
        amount = MEMBERSHIP_FEE
    
    # Get or create member profile
    member = None
    if hasattr(user, "member_profile"):
        member = user.member_profile
    
    payment = Payment.objects.create(
        user=user,
        member=member,
        amount=amount,
        payment_type=Payment.PaymentType.MEMBERSHIP,
        status=Payment.PaymentStatus.PENDING,
        payment_method=payment_method,
        notes=notes,
    )
    
    return payment


def complete_membership_payment(payment, transaction_id="", payment_method="", subscription_years=None):
    """Mark a membership payment as completed and activate member.
    
    Args:
        payment: Payment instance
        transaction_id: Optional transaction ID
        payment_method: Optional payment method
        subscription_years: Optional number of years for subscription (defaults to DEFAULT_SUBSCRIPTION_DURATION_YEARS)
    """
    from .models import Member
    
    # Update payment status
    payment.status = Payment.PaymentStatus.COMPLETED
    payment.paid_at = timezone.now()
    if transaction_id:
        payment.transaction_id = transaction_id
    if payment_method:
        payment.payment_method = payment_method
    payment.save()
    
    # Create or update member profile
    if not payment.member:
        if not hasattr(payment.user, "member_profile"):
            member = Member.objects.create(
                user=payment.user,
                status=Member.MembershipStatus.ACTIVE,
            )
        else:
            member = payment.user.member_profile
        payment.member = member
        payment.save(update_fields=["member"])
    else:
        member = payment.member
    
    # Set or extend membership expiry date
    if subscription_years is None:
        subscription_years = get_default_subscription_duration_years()
    
    # Calculate expiry date from payment date
    expiry_date = payment.paid_at.date() + timedelta(days=365 * subscription_years)
    
    # If member already has an expiry date that's in the future, extend from that date
    # Otherwise, set from payment date
    if member.membership_expiry and member.membership_expiry > payment.paid_at.date():
        expiry_date = member.membership_expiry + timedelta(days=365 * subscription_years)
    
    member.membership_expiry = expiry_date
    
    # Activate member if not already active
    if member.status != Member.MembershipStatus.ACTIVE:
        member.status = Member.MembershipStatus.ACTIVE
    
    member.save()
    
    # Update user role if needed
    if payment.user.role == User.Role.PUBLIC:
        payment.user.role = User.Role.MEMBER
        payment.user.save()
    
    return member


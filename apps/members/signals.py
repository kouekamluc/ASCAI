"""
Signals for members app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.dashboard.models import Payment
from .payment_utils import complete_membership_payment
from .models import MemberApplication


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


@receiver(post_save, sender=MemberApplication)
def notify_member_application(sender, instance, created, **kwargs):
    """Send notifications when member application status changes."""
    if created:
        # Notify admins about new application
        from apps.accounts.models import User
        admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
        
        subject = _("New Membership Application: %(name)s") % {"name": instance.user.full_name}
        
        for admin in admins:
            try:
                context = {
                    "admin": admin,
                    "applicant": instance.user,
                    "application": instance,
                }
                html_message = render_to_string("members/emails/new_application_notification.html", context)
                plain_message = _("A new membership application has been submitted by %(name)s (%(email)s).") % {
                    "name": instance.user.full_name,
                    "email": instance.user.email
                }
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            except Exception:
                pass
    else:
        # Application status changed - notify applicant
        if instance.status == MemberApplication.ApplicationStatus.APPROVED:
            subject = _("Membership Application Approved - ASCAI")
            template = "members/emails/application_approved.html"
        elif instance.status == MemberApplication.ApplicationStatus.REJECTED:
            subject = _("Membership Application Update - ASCAI")
            template = "members/emails/application_rejected.html"
        else:
            return
        
        try:
            context = {
                "applicant": instance.user,
                "application": instance,
            }
            html_message = render_to_string(template, context)
            plain_message = _("Your membership application status has been updated to: %(status)s") % {
                "status": instance.get_status_display()
            }
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            pass


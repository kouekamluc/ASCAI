"""
Celery tasks for members app.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _


@shared_task
def send_bulk_email(subject, message, recipient_list, send_as_html=True):
    """Send bulk email to list of recipients."""
    for recipient_email in recipient_list:
        try:
            if send_as_html:
                html_message = f"<html><body><p>{message.replace(chr(10), '<br>')}</p></body></html>"
            else:
                html_message = None
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # Log error but continue with other recipients
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send bulk email to {recipient_email}: {e}")


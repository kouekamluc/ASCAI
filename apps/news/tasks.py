"""
Celery tasks for news notifications.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.sites.models import Site
from .models import NewsPost
from apps.accounts.models import User


@shared_task
def send_news_notification(news_id):
    """Send email notification when a new news post is published."""
    try:
        news = NewsPost.objects.select_related('author', 'category').get(id=news_id)
        
        # Only send if published and public
        if not news.is_published or news.visibility != NewsPost.Visibility.PUBLIC:
            return
        
        # Get recipients based on visibility
        if news.visibility == NewsPost.Visibility.PUBLIC:
            # Send to all active members
            recipients = User.objects.filter(is_active=True, is_member=True)
        elif news.visibility == NewsPost.Visibility.MEMBERS_ONLY:
            # Send to all members
            recipients = User.objects.filter(is_active=True, is_member=True)
        else:
            # Board only - don't send mass notification
            return
        
        site = Site.objects.get_current()
        protocol = "https" if not settings.DEBUG else "http"
        news_url = f"{protocol}://{site.domain}{news.get_absolute_url()}"
        
        subject = _("New Announcement: {}").format(news.title)
        
        for recipient in recipients:
            # Check notification preferences (if implemented)
            # For now, send to all
            
            context = {
                "news": news,
                "recipient": recipient,
                "news_url": news_url,
                "site": site,
            }
            
            html_message = render_to_string("news/emails/new_post.html", context)
            plain_message = f"""
{_('New Announcement')}

{news.title}

{news.excerpt or news.content[:200]}...

{_('Read more')}: {news_url}
            """.strip()
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Log error but continue with other recipients
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send news notification to {recipient.email}: {e}")
        
    except NewsPost.DoesNotExist:
        pass


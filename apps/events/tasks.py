"""
Celery tasks for event management.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from .models import Event, EventRegistration, EventReminder


@shared_task
def send_registration_confirmation(registration_id):
    """Send confirmation email when user registers for an event."""
    try:
        registration = EventRegistration.objects.select_related('user', 'event').get(id=registration_id)
        event = registration.event
        user = registration.user
        
        # Check if reminder already sent
        if EventReminder.objects.filter(
            registration=registration,
            reminder_type=EventReminder.ReminderType.REGISTRATION
        ).exists():
            return
        
        # Determine email content based on status
        if registration.status == EventRegistration.Status.WAITLISTED:
            subject = _("Waitlist Confirmation: {}").format(event.title)
            template_name = "events/emails/waitlist_confirmation.html"
        else:
            subject = _("Registration Confirmation: {}").format(event.title)
            template_name = "events/emails/registration_confirmation.html"
        
        # Render email template
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        protocol = "http" if settings.DEBUG else "https"
        event_url = f"{protocol}://{site.domain}{event.get_absolute_url()}"
        
        context = {
            "event": event,
            "registration": registration,
            "user": user,
            "event_url": event_url,
        }
        
        html_message = render_to_string(template_name, context)
        plain_message = f"""
{_('Event Registration Confirmation')}

{_('Event')}: {event.title}
{_('Date')}: {event.start_date.strftime('%B %d, %Y at %I:%M %p')}
{_('Location')}: {event.location}

{_('You have successfully registered for this event.')}
        """.strip()
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Record reminder
        EventReminder.objects.create(
            event=event,
            registration=registration,
            reminder_type=EventReminder.ReminderType.REGISTRATION,
            recipient_email=user.email,
        )
        
    except EventRegistration.DoesNotExist:
        pass  # Registration was deleted or doesn't exist


@shared_task
def send_waitlist_promotion(registration_id):
    """Send email when waitlisted user is promoted to registered."""
    try:
        registration = EventRegistration.objects.select_related('user', 'event').get(id=registration_id)
        event = registration.event
        user = registration.user
        
        subject = _("Event Registration Available: {}").format(event.title)
        
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        protocol = "http" if settings.DEBUG else "https"
        event_url = f"{protocol}://{site.domain}{event.get_absolute_url()}"
        
        context = {
            "event": event,
            "registration": registration,
            "user": user,
            "event_url": event_url,
        }
        
        html_message = render_to_string("events/emails/waitlist_promotion.html", context)
        plain_message = f"""
{_('Event Registration Available')}

{_('Good news! A space has become available for the event:')}
{event.title}

{_('Date')}: {event.start_date.strftime('%B %d, %Y at %I:%M %p')}
{_('Location')}: {event.location}

{_('You have been automatically registered for this event.')}
        """.strip()
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Record reminder
        EventReminder.objects.create(
            event=event,
            registration=registration,
            reminder_type=EventReminder.ReminderType.UPDATE,
            recipient_email=user.email,
        )
        
    except EventRegistration.DoesNotExist:
        pass


@shared_task
def send_event_reminders_batch(event_ids=None, days_before_list=None):
    """Send reminders for events X days before they start."""
    if days_before_list is None:
        days_before_list = [7, 3, 1]  # Default: 7 days, 3 days, and 1 day before
    
    if event_ids:
        events = Event.objects.filter(id__in=event_ids, is_published=True)
    else:
        events = Event.objects.filter(is_published=True)
    
    now = timezone.now()
    
    for event in events:
        if event.start_date <= now:
            continue  # Event already started
        
        # Calculate days until event
        days_until = (event.start_date.date() - now.date()).days
        
        # Check if we should send reminder for this days_before value
        for days_before in days_before_list:
            if days_until == days_before:
                # Get all registered users
                registrations = EventRegistration.objects.filter(
                    event=event,
                    status__in=[
                        EventRegistration.Status.REGISTERED,
                        EventRegistration.Status.WAITLISTED
                    ]
                ).select_related('user')
                
                for registration in registrations:
                    # Check if reminder already sent
                    if EventReminder.objects.filter(
                        event=event,
                        registration=registration,
                        reminder_type=EventReminder.ReminderType.DAYS_BEFORE,
                        days_before=days_before
                    ).exists():
                        continue
                    
                    # Send reminder
                    subject = _("Event Reminder: {} ({} days)").format(event.title, days_before)
                    
                    from django.contrib.sites.models import Site
                    site = Site.objects.get_current()
                    event_url = f"https://{site.domain}{event.get_absolute_url()}"
                    
                    context = {
                        "event": event,
                        "registration": registration,
                        "user": registration.user,
                        "days_before": days_before,
                        "event_url": event_url,
                    }
                    
                    html_message = render_to_string("events/emails/event_reminder.html", context)
                    plain_message = f"""
{_('Event Reminder')}

{_('This is a reminder that you are registered for:')}
{event.title}

{_('Date')}: {event.start_date.strftime('%B %d, %Y at %I:%M %p')}
{_('Location')}: {event.location}

{_('The event is in')} {days_before} {_('day(s)')}.
                    """.strip()
                    
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[registration.user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    # Record reminder
                    EventReminder.objects.create(
                        event=event,
                        registration=registration,
                        reminder_type=EventReminder.ReminderType.DAYS_BEFORE,
                        days_before=days_before,
                        recipient_email=registration.user.email,
                    )


@shared_task
def send_event_update_notification(event_id):
    """Send notification when event details are updated."""
    try:
        event = Event.objects.get(id=event_id)
        
        # Get all registered users
        registrations = EventRegistration.objects.filter(
            event=event,
            status__in=[
                EventRegistration.Status.REGISTERED,
                EventRegistration.Status.WAITLISTED
            ]
        ).select_related('user')
        
        subject = _("Event Update: {}").format(event.title)
        
        for registration in registrations:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            event_url = f"https://{site.domain}{event.get_absolute_url()}"
            
            context = {
                "event": event,
                "registration": registration,
                "user": registration.user,
                "event_url": event_url,
            }
            
            html_message = render_to_string("events/emails/event_update.html", context)
            plain_message = f"""
{_('Event Update')}

{_('The event you are registered for has been updated:')}
{event.title}

{_('Date')}: {event.start_date.strftime('%B %d, %Y at %I:%M %p')}
{_('Location')}: {event.location}

{_('Please check the event page for more details.')}
            """.strip()
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Record reminder
            EventReminder.objects.create(
                event=event,
                registration=registration,
                reminder_type=EventReminder.ReminderType.UPDATE,
                recipient_email=registration.user.email,
            )
            
    except Event.DoesNotExist:
        pass


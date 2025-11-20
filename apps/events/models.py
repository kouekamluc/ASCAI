"""
Event management models for ASCAI platform.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.utils import sanitize_html, optimize_image


class EventCategory(models.Model):
    """Category for events."""
    
    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("description"), blank=True)
    color = models.CharField(_("color"), max_length=7, default="#3498db", help_text=_("Hex color code (e.g., #3498db)"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("event category")
        verbose_name_plural = _("event categories")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class Event(models.Model):
    """Event model."""
    
    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        MEMBERS_ONLY = "members", _("Members Only")
        BOARD_ONLY = "board", _("Board Only")
    
    # Basic information
    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(_("description"))
    location = models.CharField(_("location"), max_length=200)
    
    # Dates
    start_date = models.DateTimeField(_("start date"))
    end_date = models.DateTimeField(_("end date"))
    
    # Organization
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
        verbose_name=_("organizer"),
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=_("category"),
    )
    
    # Registration settings
    is_registration_required = models.BooleanField(_("registration required"), default=True)
    max_attendees = models.PositiveIntegerField(_("max attendees"), null=True, blank=True, help_text=_("Leave empty for unlimited"))
    registration_deadline = models.DateTimeField(_("registration deadline"), null=True, blank=True)
    
    # Visibility and status
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        verbose_name=_("visibility"),
    )
    is_published = models.BooleanField(_("published"), default=False)
    
    # Media
    featured_image = models.ImageField(
        _("featured image"),
        upload_to="events/",
        blank=True,
        null=True,
    )
    
    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    views_count = models.PositiveIntegerField(_("views"), default=0)
    
    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(fields=["-start_date"]),
            models.Index(fields=["category"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["is_published", "start_date"]),
            models.Index(fields=["is_published", "created_at"]),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"slug": self.slug})
    
    def clean(self):
        """Validate and sanitize content."""
        super().clean()
        # Sanitize HTML description
        if self.description:
            self.description = sanitize_html(self.description)
    
    def save(self, *args, **kwargs):
        """Override save to sanitize content and optimize images."""
        # Sanitize description
        self.full_clean()
        
        # Optimize featured image if provided
        if self.featured_image and hasattr(self.featured_image, 'file'):
            try:
                optimized_image = optimize_image(self.featured_image)
                self.featured_image = optimized_image
            except Exception:
                # If optimization fails, continue with original
                pass
        
        super().save(*args, **kwargs)
    
    def can_view(self, user):
        """Check if user can view this event."""
        if self.visibility == self.Visibility.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.visibility == self.Visibility.MEMBERS_ONLY:
            return user.is_member()
        if self.visibility == self.Visibility.BOARD_ONLY:
            return user.is_board_member()
        return False
    
    def can_register(self, user):
        """Check if user can register for this event."""
        if not self.is_registration_required:
            return False
        if not user.is_authenticated:
            return False
        
        # Check visibility
        if self.visibility == self.Visibility.MEMBERS_ONLY and not user.is_member():
            return False
        if self.visibility == self.Visibility.BOARD_ONLY and not user.is_board_member():
            return False
        
        # Check if registration is still open
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        
        # Check if already registered
        if EventRegistration.objects.filter(user=user, event=self, status__in=[
            EventRegistration.Status.REGISTERED, EventRegistration.Status.WAITLISTED
        ]).exists():
            return False
        
        # Check if event has started
        if timezone.now() > self.start_date:
            return False
        
        return True
    
    @property
    def registered_count(self):
        """Get count of registered attendees."""
        return self.registrations.filter(status=EventRegistration.Status.REGISTERED).count()
    
    @property
    def waitlist_count(self):
        """Get count of waitlisted attendees."""
        return self.registrations.filter(status=EventRegistration.Status.WAITLISTED).count()
    
    @property
    def is_full(self):
        """Check if event is at capacity."""
        if self.max_attendees is None:
            return False
        return self.registered_count >= self.max_attendees
    
    @property
    def spaces_available(self):
        """Get number of available spaces."""
        if self.max_attendees is None:
            return None  # Unlimited
        return max(0, self.max_attendees - self.registered_count)
    
    def is_upcoming(self):
        """Check if event is in the future."""
        return timezone.now() < self.start_date
    
    def is_past(self):
        """Check if event is in the past."""
        return timezone.now() > self.end_date


class EventRegistration(models.Model):
    """Event registration/RSVP model."""
    
    class Status(models.TextChoices):
        REGISTERED = "registered", _("Registered")
        WAITLISTED = "waitlisted", _("Waitlisted")
        CANCELLED = "cancelled", _("Cancelled")
        ATTENDED = "attended", _("Attended")
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
        verbose_name=_("user"),
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("event"),
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.REGISTERED,
        verbose_name=_("status"),
    )
    registered_at = models.DateTimeField(_("registered at"), auto_now_add=True)
    checked_in_at = models.DateTimeField(_("checked in at"), null=True, blank=True)
    
    # Additional information
    dietary_requirements = models.TextField(_("dietary requirements"), blank=True)
    special_requests = models.TextField(_("special requests"), blank=True)
    admin_notes = models.TextField(_("admin notes"), blank=True, help_text=_("Internal notes visible only to admins"))
    
    class Meta:
        verbose_name = _("event registration")
        verbose_name_plural = _("event registrations")
        ordering = ["registered_at"]
        unique_together = [["user", "event"]]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["registered_at"]),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.event.title}"
    
    def check_in(self):
        """Mark attendee as checked in."""
        self.status = self.Status.ATTENDED
        self.checked_in_at = timezone.now()
        self.save(update_fields=["status", "checked_in_at"])


class EventReminder(models.Model):
    """Track sent event reminders."""
    
    class ReminderType(models.TextChoices):
        REGISTRATION = "registration", _("Registration Confirmation")
        DAYS_BEFORE = "days_before", _("Days Before Event")
        UPDATE = "update", _("Event Update")
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name=_("event"),
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name="reminders",
        null=True,
        blank=True,
        verbose_name=_("registration"),
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        verbose_name=_("reminder type"),
    )
    days_before = models.IntegerField(_("days before"), null=True, blank=True, help_text=_("Days before event (for DAYS_BEFORE type)"))
    sent_at = models.DateTimeField(_("sent at"), auto_now_add=True)
    recipient_email = models.EmailField(_("recipient email"))
    
    class Meta:
        verbose_name = _("event reminder")
        verbose_name_plural = _("event reminders")
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["event", "reminder_type"]),
            models.Index(fields=["sent_at"]),
        ]
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.event.title} - {self.recipient_email}"

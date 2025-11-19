"""
Content models for manageable public-facing content.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse


class University(models.Model):
    """University model for the Students page."""
    name = models.CharField(_("University Name"), max_length=200)
    url = models.URLField(_("Website URL"), blank=True)
    description = models.TextField(_("Description"), blank=True)
    location = models.CharField(_("Location"), max_length=100, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="universities/logos/", blank=True, null=True, help_text=_("University logo (recommended: 200x200px)"))
    image = models.ImageField(_("University Image"), upload_to="universities/images/", blank=True, null=True, help_text=_("Featured image of the university (recommended: 800x600px)"))
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0, help_text=_("Lower numbers appear first"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("University")
        verbose_name_plural = _("Universities")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ExchangeProgram(models.Model):
    """Exchange program model for the Students page."""
    name = models.CharField(_("Program Name"), max_length=200)
    description = models.TextField(_("Description"))
    url = models.URLField(_("Program URL"), blank=True)
    icon = models.CharField(
        _("Icon Name"),
        max_length=50,
        default="exchange",
        help_text=_("Icon identifier (e.g., 'erasmus', 'exchange', 'study-abroad')")
    )
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Exchange Program")
        verbose_name_plural = _("Exchange Programs")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    """Testimonial/Success Story model for the Diaspora page."""
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonials",
        verbose_name=_("Member")
    )
    name = models.CharField(_("Name"), max_length=200, help_text=_("Name if not linked to a member"))
    university = models.CharField(_("University"), max_length=200, blank=True)
    content = models.TextField(_("Testimonial Content"))
    photo = models.ImageField(_("Photo"), upload_to="testimonials/photos/", blank=True, null=True)
    is_featured = models.BooleanField(_("Featured"), default=False)
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Testimonial")
        verbose_name_plural = _("Testimonials")
        ordering = ['display_order', '-created_at']

    def __str__(self):
        if self.member:
            return f"{self.member.full_name} - Testimonial"
        return f"{self.name} - Testimonial"

    @property
    def display_name(self):
        """Get display name (member name or custom name)."""
        if self.member:
            return self.member.full_name
        return self.name

    @property
    def display_university(self):
        """Get display university (member university or custom university)."""
        if self.member and hasattr(self.member, 'member_profile') and self.member.member_profile.university:
            return self.member.member_profile.university
        return self.university or ""


class UsefulLinkCategory(models.Model):
    """Category for organizing useful links."""
    name = models.CharField(_("Category Name"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True)
    description = models.TextField(_("Description"), blank=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Link Category")
        verbose_name_plural = _("Link Categories")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class UsefulLink(models.Model):
    """Useful link model for the Resources page."""
    category = models.ForeignKey(
        UsefulLinkCategory,
        on_delete=models.CASCADE,
        related_name="links",
        verbose_name=_("Category")
    )
    name = models.CharField(_("Link Name"), max_length=200)
    url = models.URLField(_("URL"))
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(
        _("Icon Name"),
        max_length=50,
        blank=True,
        help_text=_("Optional icon identifier")
    )
    is_external = models.BooleanField(_("External Link"), default=True, help_text=_("Opens in new tab"))
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Useful Link")
        verbose_name_plural = _("Useful Links")
        ordering = ['category', 'display_order', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ContactInfo(models.Model):
    """Contact information model for the Contact page."""
    CONTACT_TYPE_CHOICES = [
        ('general', _('General Inquiries')),
        ('students', _('Student Support')),
        ('membership', _('Membership')),
        ('partnerships', _('Partnerships')),
        ('other', _('Other')),
    ]

    contact_type = models.CharField(
        _("Contact Type"),
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        default='general'
    )
    label = models.CharField(_("Label"), max_length=200, help_text=_("Display label (e.g., 'General Inquiries')"))
    email = models.EmailField(_("Email Address"))
    phone = models.CharField(_("Phone Number"), max_length=50, blank=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Contact Information")
        verbose_name_plural = _("Contact Information")
        ordering = ['display_order', 'contact_type']

    def __str__(self):
        return f"{self.label} - {self.email}"


class OfficeHours(models.Model):
    """Office hours model for the Contact page."""
    DAY_CHOICES = [
        ('monday', _('Monday')),
        ('tuesday', _('Tuesday')),
        ('wednesday', _('Wednesday')),
        ('thursday', _('Thursday')),
        ('friday', _('Friday')),
        ('saturday', _('Saturday')),
        ('sunday', _('Sunday')),
    ]

    day = models.CharField(_("Day"), max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    is_closed = models.BooleanField(_("Closed"), default=False)
    notes = models.CharField(_("Notes"), max_length=200, blank=True, help_text=_("e.g., 'Public Reception'"))
    is_active = models.BooleanField(_("Active"), default=True)
    display_order = models.IntegerField(_("Display Order"), default=0)

    class Meta:
        verbose_name = _("Office Hour")
        verbose_name_plural = _("Office Hours")
        ordering = ['display_order', 'day']
        unique_together = ['day', 'start_time']

    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_display()} - Closed"
        return f"{self.get_day_display()} - {self.start_time} to {self.end_time}"


class ContactFormSubmission(models.Model):
    """Model to store contact form submissions from the website."""
    
    class Status(models.TextChoices):
        NEW = "new", _("New")
        IN_PROGRESS = "in_progress", _("In Progress")
        RESPONDED = "responded", _("Responded")
        CLOSED = "closed", _("Closed")
    
    name = models.CharField(_("Name"), max_length=200)
    email = models.EmailField(_("Email Address"))
    subject = models.CharField(_("Subject"), max_length=200)
    message = models.TextField(_("Message"))
    contact_type = models.CharField(
        _("Contact Type"),
        max_length=20,
        choices=ContactInfo.CONTACT_TYPE_CHOICES,
        default='general'
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    recipient_email = models.EmailField(_("Recipient Email"), help_text=_("Email address where the message was sent"))
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.CharField(_("User Agent"), max_length=500, blank=True)
    notes = models.TextField(_("Internal Notes"), blank=True, help_text=_("Internal notes for staff"))
    responded_at = models.DateTimeField(_("Responded At"), null=True, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_responses",
        verbose_name=_("Responded By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Contact Form Submission")
        verbose_name_plural = _("Contact Form Submissions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['contact_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def mark_as_responded(self, user=None):
        """Mark submission as responded."""
        from django.utils import timezone
        self.status = self.Status.RESPONDED
        self.responded_at = timezone.now()
        if user:
            self.responded_by = user
        self.save(update_fields=['status', 'responded_at', 'responded_by', 'updated_at'])

"""
Admin interface for events app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Event, EventCategory, EventRegistration, EventReminder


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    """Admin for event categories."""
    list_display = ["name", "slug", "color_display", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    
    def color_display(self, obj):
        """Display color as a colored box."""
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc;"></span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = _("Color")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for events."""
    list_display = [
        "title",
        "organizer",
        "category",
        "start_date",
        "location",
        "registered_count_display",
        "is_published",
        "visibility",
        "created_at",
    ]
    list_filter = [
        "is_published",
        "visibility",
        "category",
        "start_date",
        "created_at",
    ]
    search_fields = [
        "title",
        "description",
        "location",
        "organizer__email",
        "organizer__first_name",
        "organizer__last_name",
    ]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "views_count"]
    date_hierarchy = "start_date"
    
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("title", "slug", "description", "location", "featured_image")
        }),
        (_("Date & Time"), {
            "fields": ("start_date", "end_date")
        }),
        (_("Organization"), {
            "fields": ("organizer", "category", "visibility")
        }),
        (_("Registration"), {
            "fields": (
                "is_registration_required",
                "max_attendees",
                "registration_deadline"
            )
        }),
        (_("Status"), {
            "fields": ("is_published",)
        }),
        (_("Metadata"), {
            "fields": ("created_at", "updated_at", "views_count"),
            "classes": ("collapse",)
        }),
    )
    
    def registered_count_display(self, obj):
        """Display registered count with link to attendees."""
        registered = obj.registered_count
        waitlisted = obj.waitlist_count
        url = reverse("admin:events_eventregistration_changelist")
        url += f"?event__id__exact={obj.id}"
        
        if obj.max_attendees:
            return format_html(
                '<a href="{}">{} / {}</a> ({} waitlisted)',
                url,
                registered,
                obj.max_attendees,
                waitlisted
            )
        return format_html(
            '<a href="{}">{}</a> ({} waitlisted)',
            url,
            registered,
            waitlisted
        )
    registered_count_display.short_description = _("Registrations")
    
    actions = ["publish_events", "unpublish_events", "send_reminders"]
    
    def publish_events(self, request, queryset):
        """Publish selected events."""
        count = queryset.update(is_published=True)
        self.message_user(request, _("{} events published.").format(count))
    publish_events.short_description = _("Publish selected events")
    
    def unpublish_events(self, request, queryset):
        """Unpublish selected events."""
        count = queryset.update(is_published=False)
        self.message_user(request, _("{} events unpublished.").format(count))
    unpublish_events.short_description = _("Unpublish selected events")
    
    def send_reminders(self, request, queryset):
        """Send reminders for selected events."""
        from .tasks import send_event_reminders_batch
        from .utils import safe_task_execute
        count = queryset.count()
        event_ids = list(queryset.values_list("id", flat=True))
        safe_task_execute(send_event_reminders_batch, event_ids)
        self.message_user(
            request,
            _("Reminders sent for {} events.").format(count)
        )
    send_reminders.short_description = _("Send reminders for selected events")


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    """Admin for event registrations."""
    list_display = [
        "user",
        "event",
        "status",
        "registered_at",
        "checked_in_at",
        "event_start_date",
    ]
    list_filter = [
        "status",
        "registered_at",
        "event__category",
        "event__start_date",
    ]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "event__title",
    ]
    readonly_fields = ["registered_at"]
    date_hierarchy = "registered_at"
    
    fieldsets = (
        (_("Registration"), {
            "fields": ("user", "event", "status", "registered_at")
        }),
        (_("Check-in"), {
            "fields": ("checked_in_at",)
        }),
        (_("Additional Information"), {
            "fields": ("dietary_requirements", "special_requests")
        }),
        (_("Admin Notes"), {
            "fields": ("admin_notes",)
        }),
    )
    
    def event_start_date(self, obj):
        """Display event start date."""
        return obj.event.start_date
    event_start_date.short_description = _("Event Date")
    event_start_date.admin_order_field = "event__start_date"
    
    actions = ["mark_as_attended", "mark_as_cancelled", "export_csv"]
    
    def mark_as_attended(self, request, queryset):
        """Mark selected registrations as attended."""
        count = 0
        for reg in queryset:
            if reg.status in [EventRegistration.Status.REGISTERED, EventRegistration.Status.WAITLISTED]:
                reg.check_in()
                count += 1
        self.message_user(request, _("{} registrations marked as attended.").format(count))
    mark_as_attended.short_description = _("Mark selected as attended")
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected registrations as cancelled."""
        count = queryset.update(status=EventRegistration.Status.CANCELLED)
        self.message_user(request, _("{} registrations cancelled.").format(count))
    mark_as_cancelled.short_description = _("Cancel selected registrations")
    
    def export_csv(self, request, queryset):
        """Export selected registrations to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="registrations.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            _("User"),
            _("Email"),
            _("Event"),
            _("Status"),
            _("Registered At"),
            _("Checked In At"),
            _("Dietary Requirements"),
            _("Special Requests"),
        ])
        
        for reg in queryset.select_related("user", "event"):
            writer.writerow([
                reg.user.full_name,
                reg.user.email,
                reg.event.title,
                reg.get_status_display(),
                reg.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
                reg.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if reg.checked_in_at else "",
                reg.dietary_requirements,
                reg.special_requests,
            ])
        
        return response
    export_csv.short_description = _("Export selected to CSV")


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    """Admin for event reminders."""
    list_display = [
        "event",
        "reminder_type",
        "days_before",
        "recipient_email",
        "sent_at",
    ]
    list_filter = [
        "reminder_type",
        "sent_at",
    ]
    search_fields = [
        "event__title",
        "recipient_email",
    ]
    readonly_fields = ["sent_at"]
    date_hierarchy = "sent_at"

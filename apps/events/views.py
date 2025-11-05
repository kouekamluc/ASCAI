"""
Views for events app.
"""

import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.utils.text import slugify
from django.core.cache import cache
from .models import Event, EventCategory, EventRegistration, EventReminder
from .forms import EventForm, RegistrationForm, EventFilterForm, EventCategoryForm


def event_list(request):
    """List all published events."""
    # Use cache for categories list (not user-specific)
    cache_key = 'event_categories_list'
    categories = cache.get(cache_key)
    if categories is None:
        categories = list(EventCategory.objects.all())
        cache.set(cache_key, categories, 60 * 15)  # Cache for 15 minutes
    
    events = Event.objects.filter(is_published=True).select_related('category', 'organizer')
    
    # Filter by visibility
    if request.user.is_authenticated:
        if request.user.is_board_member():
            pass  # Board members can see all
        elif request.user.is_member():
            events = events.exclude(visibility=Event.Visibility.BOARD_ONLY)
        else:
            events = events.filter(visibility=Event.Visibility.PUBLIC)
    else:
        events = events.filter(visibility=Event.Visibility.PUBLIC)
    
    # Apply filters
    filter_form = EventFilterForm(request.GET)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get("search")
        category = filter_form.cleaned_data.get("category")
        date_from = filter_form.cleaned_data.get("date_from")
        date_to = filter_form.cleaned_data.get("date_to")
        visibility = filter_form.cleaned_data.get("visibility")
        
        if search:
            events = events.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        if category:
            events = events.filter(category=category)
        
        if date_from:
            events = events.filter(start_date__gte=date_from)
        
        if date_to:
            events = events.filter(start_date__lte=date_to)
        
        if visibility:
            events = events.filter(visibility=visibility)
    
    # Filter by time (upcoming, past, all)
    time_filter = request.GET.get("time", "upcoming")
    if time_filter == "upcoming":
        events = events.filter(start_date__gte=timezone.now())
    elif time_filter == "past":
        events = events.filter(end_date__lt=timezone.now())
    # "all" shows everything
    
    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "filter_form": filter_form,
        "categories": categories,
        "time_filter": time_filter,
    }
    
    return render(request, "events/list.html", context)


def event_detail(request, slug):
    """Detail view for an event."""
    event = get_object_or_404(Event, slug=slug)
    
    # Check visibility
    if not event.can_view(request.user):
        messages.error(request, _("You don't have permission to view this event."))
        return redirect("events:list")
    
    # Check if user is registered (exclude cancelled status for display)
    registration = None
    cancelled_registration = None
    if request.user.is_authenticated:
        # Get active registration (REGISTERED, WAITLISTED, or ATTENDED)
        registration = EventRegistration.objects.filter(
            user=request.user,
            event=event,
            status__in=[
                EventRegistration.Status.REGISTERED,
                EventRegistration.Status.WAITLISTED,
                EventRegistration.Status.ATTENDED
            ]
        ).first()
        # Also check for cancelled registration separately
        if not registration:
            cancelled_registration = EventRegistration.objects.filter(
                user=request.user,
                event=event,
                status=EventRegistration.Status.CANCELLED
            ).first()
    
    # Registration form
    registration_form = None
    if request.user.is_authenticated and event.can_register(request.user):
        registration_form = RegistrationForm(event=event)
    
    # Increment views
    event.views_count += 1
    event.save(update_fields=["views_count"])
    
    context = {
        "event": event,
        "registration": registration,
        "cancelled_registration": cancelled_registration,
        "registration_form": registration_form,
        "can_register": event.can_register(request.user) if request.user.is_authenticated else False,
        "now": timezone.now(),
    }
    
    return render(request, "events/detail.html", context)


def event_calendar(request):
    """Calendar view for events."""
    return render(request, "events/calendar.html")


def event_calendar_feed(request):
    """JSON feed for FullCalendar.js."""
    events = Event.objects.filter(is_published=True)
    
    # Filter by visibility
    if request.user.is_authenticated:
        if request.user.is_board_member():
            pass  # Board members can see all
        elif request.user.is_member():
            events = events.exclude(visibility=Event.Visibility.BOARD_ONLY)
        else:
            events = events.filter(visibility=Event.Visibility.PUBLIC)
    else:
        events = events.filter(visibility=Event.Visibility.PUBLIC)
    
    # Date range filter (for FullCalendar)
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        try:
            from datetime import datetime
            start_date = datetime.fromisoformat(start.replace("Z", "+00:00"))
            events = events.filter(start_date__gte=start_date)
        except (ValueError, AttributeError):
            pass
    if end:
        try:
            from datetime import datetime
            end_date = datetime.fromisoformat(end.replace("Z", "+00:00"))
            events = events.filter(start_date__lte=end_date)
        except (ValueError, AttributeError):
            pass
    
    # Format events for FullCalendar
    events_list = []
    for event in events:
        events_list.append({
            "id": event.id,
            "title": event.title,
            "start": event.start_date.isoformat(),
            "end": event.end_date.isoformat(),
            "url": event.get_absolute_url(),
            "color": event.category.color if event.category else "#3498db",
            "extendedProps": {
                "location": event.location,
                "slug": event.slug,
            },
        })
    
    return JsonResponse(events_list, safe=False)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def event_create(request):
    """Create a new event."""
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            if not event.organizer_id:
                event.organizer = request.user
            
            # Generate slug from title
            if not event.slug:
                base_slug = slugify(event.title)
                slug = base_slug
                counter = 1
                while Event.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                event.slug = slug
            
            event.save()
            messages.success(request, _("Event created successfully."))
            return redirect("events:detail", slug=event.slug)
    else:
        form = EventForm(user=request.user)
    
    return render(request, "events/form.html", {"form": form, "action": _("Create")})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def event_edit(request, slug):
    """Edit an existing event."""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permission
    if event.organizer != request.user and not request.user.is_admin():
        messages.error(request, _("You can only edit events you organized."))
        return redirect("events:detail", slug=event.slug)
    
    if request.method == "POST":
        form = EventForm(
            request.POST,
            request.FILES,
            instance=event,
            user=request.user,
        )
        if form.is_valid():
            event = form.save()
            messages.success(request, _("Event updated successfully."))
            return redirect("events:detail", slug=event.slug)
    else:
        form = EventForm(instance=event, user=request.user)
    
    return render(request, "events/form.html", {
        "form": form,
        "event": event,
        "action": _("Edit"),
    })


@login_required
@user_passes_test(lambda u: u.is_board_member())
def event_delete(request, slug):
    """Delete an event."""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permission
    if event.organizer != request.user and not request.user.is_admin():
        messages.error(request, _("You can only delete events you organized."))
        return redirect("events:detail", slug=event.slug)
    
    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully."))
        return redirect("events:list")
    
    return render(request, "events/delete_confirm.html", {"event": event})


@login_required
@require_http_methods(["POST"])
def event_register(request, slug):
    """Register for an event."""
    event = get_object_or_404(Event, slug=slug)
    
    if not event.can_register(request.user):
        messages.error(request, _("You cannot register for this event."))
        return redirect("events:detail", slug=event.slug)
    
    form = RegistrationForm(request.POST, event=event)
    if form.is_valid():
        with transaction.atomic():
            # Check if user has a cancelled registration (for re-registration)
            existing_registration = EventRegistration.objects.filter(
                user=request.user,
                event=event,
                status=EventRegistration.Status.CANCELLED
            ).first()
            
            if existing_registration:
                # Re-register by updating the cancelled registration
                registration = existing_registration
                registration.dietary_requirements = form.cleaned_data.get('dietary_requirements', '')
                registration.special_requests = form.cleaned_data.get('special_requests', '')
                # Reset check-in info if it exists
                registration.checked_in_at = None
            else:
                # Create new registration
                registration = form.save(commit=False)
                registration.user = request.user
                registration.event = event
            
            # Check capacity
            if event.is_full:
                # Add to waitlist
                registration.status = EventRegistration.Status.WAITLISTED
                registration.save()
                messages.info(request, _("Event is full. You have been added to the waitlist."))
            else:
                # Register normally
                registration.status = EventRegistration.Status.REGISTERED
                registration.save()
                if existing_registration:
                    messages.success(request, _("Successfully re-registered for the event!"))
                else:
                    messages.success(request, _("Successfully registered for the event!"))
            
            # Send confirmation email (async via Celery, with fallback to sync)
            from .tasks import send_registration_confirmation
            from .utils import safe_task_execute
            safe_task_execute(send_registration_confirmation, registration.id)
        
        return redirect("events:detail", slug=event.slug)
    else:
        messages.error(request, _("There was an error with your registration."))
        return redirect("events:detail", slug=event.slug)


@login_required
@require_http_methods(["POST"])
def event_unregister(request, slug):
    """Cancel event registration."""
    event = get_object_or_404(Event, slug=slug)
    registration = EventRegistration.objects.filter(
        user=request.user,
        event=event,
        status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.WAITLISTED]
    ).first()
    
    if not registration:
        messages.error(request, _("You are not registered for this event."))
        return redirect("events:detail", slug=event.slug)
    
    with transaction.atomic():
        # Store original status before cancellation
        original_status = registration.status
        
        # Cancel registration
        registration.status = EventRegistration.Status.CANCELLED
        registration.save()
        
        # If there was a waitlist and a space opened, promote the next person
        if original_status == EventRegistration.Status.REGISTERED:
            # Find the first waitlisted person and promote them
            waitlisted = EventRegistration.objects.filter(
                event=event,
                status=EventRegistration.Status.WAITLISTED
            ).order_by("registered_at").first()
            
            if waitlisted:
                waitlisted.status = EventRegistration.Status.REGISTERED
                waitlisted.save()
                # Send notification email (async via Celery, with fallback to sync)
                from .tasks import send_waitlist_promotion
                from .utils import safe_task_execute
                safe_task_execute(send_waitlist_promotion, waitlisted.id)
        
        messages.success(request, _("Registration cancelled successfully."))
    
    return redirect("events:detail", slug=event.slug)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def event_attendees(request, slug):
    """Admin view of event attendees."""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permission
    if event.organizer != request.user and not request.user.is_admin():
        messages.error(request, _("You don't have permission to view attendees."))
        return redirect("events:detail", slug=event.slug)
    
    registrations = event.registrations.exclude(
        status=EventRegistration.Status.CANCELLED
    ).select_related("user").order_by("registered_at")
    
    # Export CSV
    if request.GET.get("export") == "csv":
        import csv
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="event_{event.slug}_attendees.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            _("Name"),
            _("Email"),
            _("Status"),
            _("Registered At"),
            _("Checked In At"),
            _("Dietary Requirements"),
            _("Special Requests"),
        ])
        
        for reg in registrations:
            writer.writerow([
                reg.user.full_name,
                reg.user.email,
                reg.get_status_display(),
                reg.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
                reg.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if reg.checked_in_at else "",
                reg.dietary_requirements,
                reg.special_requests,
            ])
        
        return response
    
    context = {
        "event": event,
        "registrations": registrations,
    }
    
    return render(request, "events/attendees.html", context)


@login_required
@user_passes_test(lambda u: u.is_board_member())
@require_http_methods(["POST"])
def event_check_in(request, slug, registration_id):
    """Check in an attendee."""
    event = get_object_or_404(Event, slug=slug)
    registration = get_object_or_404(
        EventRegistration,
        id=registration_id,
        event=event
    )
    
    # Check permission
    if event.organizer != request.user and not request.user.is_admin():
        messages.error(request, _("You don't have permission to check in attendees."))
        return redirect("events:attendees", slug=event.slug)
    
    registration.check_in()
    messages.success(request, _("Attendee checked in successfully."))
    
    return redirect("events:attendees", slug=event.slug)


# Category Management Views
@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_list(request):
    """List all event categories."""
    categories = EventCategory.objects.all().order_by("name")
    return render(request, "events/category_list.html", {"categories": categories})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_create(request):
    """Create a new event category."""
    if request.method == "POST":
        form = EventCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if not category.slug:
                base_slug = slugify(category.name)
                slug = base_slug
                counter = 1
                while EventCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                category.slug = slug
            category.save()
            messages.success(request, _("Category created successfully."))
            return redirect("events:category_list")
    else:
        form = EventCategoryForm()
    
    return render(request, "events/category_form.html", {"form": form, "action": _("Create")})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_edit(request, pk):
    """Edit an existing event category."""
    category = get_object_or_404(EventCategory, pk=pk)
    
    if request.method == "POST":
        form = EventCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category updated successfully."))
            return redirect("events:category_list")
    else:
        form = EventCategoryForm(instance=category)
    
    return render(request, "events/category_form.html", {
        "form": form,
        "category": category,
        "action": _("Edit"),
    })


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_delete(request, pk):
    """Delete an event category."""
    category = get_object_or_404(EventCategory, pk=pk)
    
    # Check if category is used by any events
    event_count = category.events.count()
    
    if request.method == "POST":
        if event_count > 0:
            messages.error(
                request,
                _("Cannot delete category. It is used by %(count)s event(s).") % {"count": event_count}
            )
        else:
            category.delete()
            messages.success(request, _("Category deleted successfully."))
        return redirect("events:category_list")
    
    return render(request, "events/category_delete_confirm.html", {
        "category": category,
        "event_count": event_count,
    })

"""
Dashboard views for ASCAI platform.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
import json
import csv

from apps.members.models import Member
from .models import Payment
from .utils import (
    get_member_stats,
    get_recent_activity,
    get_event_stats,
    get_revenue_stats,
    generate_report_data,
    get_user_dashboard_stats,
    get_user_upcoming_events,
    get_user_recent_activity,
    get_user_news_feed,
    get_user_event_chart_data,
    get_user_payment_chart_data,
    get_user_event_status_chart_data,
)


def index_view(request):
    """Public landing page."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    
    # Get latest published news posts (public visibility only)
    from apps.news.models import NewsPost
    latest_news = NewsPost.objects.filter(
        is_published=True,
        visibility=NewsPost.Visibility.PUBLIC
    ).select_related('author', 'category').order_by('-published_at', '-created_at')[:4]
    
    # Get upcoming published events (public visibility only)
    from apps.events.models import Event
    upcoming_events = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        start_date__gte=timezone.now()
    ).select_related('category', 'organizer').order_by('start_date')[:4]
    
    # Get open calls/bandi (events starting today or in the future)
    open_calls = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        start_date__gte=timezone.now()
    ).select_related('category', 'organizer').order_by('start_date')[:3]
    
    # Get closed calls/bandi (events that have ended)
    closed_calls = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        end_date__lt=timezone.now()
    ).select_related('category', 'organizer').order_by('-end_date')[:2]
    
    # Get testimonials for diaspora section
    from apps.content.models import Testimonial
    testimonials = Testimonial.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('member').order_by('display_order', '-created_at')[:2]
    
    # Get universities for university search section
    from apps.content.models import University
    universities = University.objects.filter(is_active=True).order_by('display_order', 'name')[:10]
    
    context = {
        'latest_news': latest_news,
        'upcoming_events': upcoming_events,
        'open_calls': open_calls,
        'closed_calls': closed_calls,
        'testimonials': testimonials,
        'universities': universities,
    }
    return render(request, "dashboard/index.html", context)


def students_view(request):
    """Students page with universities, scholarships, and study information."""
    from apps.events.models import Event, EventCategory
    from apps.news.models import NewsPost
    from apps.content.models import University, ExchangeProgram
    from django.db.models import Q
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get scholarship events (calls/bandi)
    scholarships = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        start_date__gte=timezone.now()
    ).select_related('category', 'organizer').order_by('start_date')[:6]
    
    # Get news related to studies/scholarships
    study_news = NewsPost.objects.filter(
        is_published=True,
        visibility=NewsPost.Visibility.PUBLIC
    ).filter(
        Q(title__icontains='scholarship') |
        Q(title__icontains='university') |
        Q(title__icontains='study') |
        Q(title__icontains='erasmus') |
        Q(excerpt__icontains='scholarship') |
        Q(excerpt__icontains='university') |
        Q(excerpt__icontains='study') |
        Q(excerpt__icontains='erasmus')
    ).select_related('author', 'category').order_by('-published_at', '-created_at')[:6]
    
    # Get universities from content model
    universities = University.objects.filter(is_active=True).order_by('display_order', 'name')
    
    # Filter universities by search query if provided
    if search_query:
        universities = universities.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get exchange programs from content model
    exchange_programs = ExchangeProgram.objects.filter(is_active=True).order_by('display_order', 'name')
    
    # Filter exchange programs by search query if provided
    if search_query:
        exchange_programs = exchange_programs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get event categories for filtering
    categories = EventCategory.objects.all()[:8]
    
    context = {
        'scholarships': scholarships,
        'study_news': study_news,
        'universities': universities,
        'exchange_programs': exchange_programs,
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, "dashboard/students.html", context)


def diaspora_view(request):
    """Diaspora page with news, events, testimonials, and success stories."""
    from apps.news.models import NewsPost
    from apps.events.models import Event
    from apps.content.models import Testimonial
    from django.core.paginator import Paginator
    
    # Get latest diaspora news
    diaspora_news = NewsPost.objects.filter(
        is_published=True,
        visibility=NewsPost.Visibility.PUBLIC
    ).select_related('author', 'category').order_by('-published_at', '-created_at')
    
    # Paginate news
    news_paginator = Paginator(diaspora_news, 9)
    news_page = request.GET.get('news_page', 1)
    news_page_obj = news_paginator.get_page(news_page)
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        start_date__gte=timezone.now()
    ).select_related('category', 'organizer').order_by('start_date')[:6]
    
    # Get past events (for testimonials context)
    past_events = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC,
        end_date__lt=timezone.now()
    ).select_related('category', 'organizer').order_by('-end_date')[:4]
    
    # Get testimonials from content model
    testimonials = Testimonial.objects.filter(is_active=True).select_related('member').order_by('display_order', '-created_at')[:6]
    
    context = {
        'news_page_obj': news_page_obj,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'testimonials': testimonials,
    }
    return render(request, "dashboard/diaspora.html", context)


def resources_view(request):
    """Resources page with useful links, documents, and downloads."""
    from apps.documents.models import Document, DocumentFolder
    from apps.content.models import UsefulLinkCategory, UsefulLink
    from django.core.paginator import Paginator
    from django.db.models import Q, Prefetch
    
    # Get all published documents
    documents = Document.objects.filter(
        is_published=True
    ).select_related('uploader', 'folder').prefetch_related('tags').order_by('-created_at')
    
    # Filter by search query
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Filter by folder
    folder_id = request.GET.get('folder')
    current_folder = None
    if folder_id:
        try:
            current_folder = DocumentFolder.objects.get(id=folder_id)
            documents = documents.filter(folder=current_folder)
        except DocumentFolder.DoesNotExist:
            pass
    
    # Permission filtering - only show documents user can view
    accessible_docs = []
    for doc in documents:
        if doc.can_view(request.user) and doc.file:  # Only include documents with files
            accessible_docs.append(doc.id)
    
    if accessible_docs:
        documents = Document.objects.filter(id__in=accessible_docs).order_by('-created_at')
    else:
        documents = Document.objects.none()
    
    # Paginate documents
    doc_paginator = Paginator(documents, 12)
    doc_page = request.GET.get('doc_page', 1)
    doc_page_obj = doc_paginator.get_page(doc_page)
    
    # Get accessible folders
    folders = DocumentFolder.objects.all()
    accessible_folders = []
    for folder in folders:
        if folder.can_access(request.user):
            accessible_folders.append(folder)
    
    # Get useful links organized by category (only active links)
    link_categories = UsefulLinkCategory.objects.filter(
        is_active=True
    ).prefetch_related(
        Prefetch('links', queryset=UsefulLink.objects.filter(is_active=True).order_by('display_order', 'name'))
    ).order_by('display_order', 'name')
    
    context = {
        'doc_page_obj': doc_page_obj,
        'accessible_folders': accessible_folders,
        'current_folder': current_folder,
        'search_query': search_query,
        'link_categories': link_categories,
    }
    return render(request, "dashboard/resources.html", context)


def contact_view(request):
    """Contact page with contact form and information."""
    from django.contrib import messages
    from django.core.mail import send_mail
    from django.conf import settings
    from apps.content.models import ContactInfo, OfficeHours
    import logging
    
    logger = logging.getLogger(__name__)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        contact_type = request.POST.get('contact_type', 'general')
        
        if name and email and subject and message:
            try:
                # Get contact email based on type, default to general
                contact_info = ContactInfo.objects.filter(
                    contact_type=contact_type,
                    is_active=True
                ).first()
                
                recipient_email = contact_info.email if contact_info else 'info@ascai.it'
                contact_label = contact_info.label if contact_info else 'General Inquiries'
                
                # Get IP address and user agent for tracking
                ip_address = request.META.get('REMOTE_ADDR', None)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
                
                # Save submission to database
                from apps.content.models import ContactFormSubmission
                submission = ContactFormSubmission.objects.create(
                    name=name,
                    email=email,
                    subject=subject,
                    message=message,
                    contact_type=contact_type,
                    recipient_email=recipient_email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status=ContactFormSubmission.Status.NEW
                )
                
                # Prepare email message for ASCAI team
                email_subject = f'ASCAI Contact Form: {subject}'
                email_message = f"""New contact form submission from ASCAI website:

From: {name}
Email: {email}
Contact Type: {contact_label}
Subject: {subject}

Message:
{message}

---
This message was sent through the ASCAI contact form.
Reply directly to: {email}
Submission ID: {submission.id}
"""
                
                # Send email to ASCAI team
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                
                # Send confirmation email to the user
                try:
                    confirmation_subject = _('Thank you for contacting ASCAI')
                    confirmation_message = f"""Dear {name},

Thank you for contacting ASCAI - Association of Cameroonian Students in Lazio.

We have received your message regarding: {subject}

Our team will review your inquiry and get back to you as soon as possible.

Your message:
{message}

Best regards,
ASCAI Team
"""
                    send_mail(
                        subject=confirmation_subject,
                        message=confirmation_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=True,  # Don't fail if confirmation email fails
                    )
                except Exception as confirm_error:
                    # Log but don't fail the whole process if confirmation email fails
                    logger.warning(f"Failed to send confirmation email to {email}: {str(confirm_error)}")
                
                logger.info(f"Contact form submitted successfully: {name} ({email}) - {subject} (ID: {submission.id})")
                messages.success(request, _('Thank you for your message! We have sent you a confirmation email and will get back to you soon.'))
                return redirect('dashboard:contact')
                
            except Exception as e:
                # Log the error for debugging
                logger.error(f"Error sending contact form email: {str(e)}", exc_info=True)
                messages.error(request, _('Sorry, there was an error sending your message. Please try again later or contact us directly at info@ascai.it'))
        else:
            messages.error(request, _('Please fill in all required fields.'))
    
    # Get contact information from models
    contact_info_list = ContactInfo.objects.filter(is_active=True).order_by('display_order', 'contact_type')
    
    # Get office hours
    office_hours = OfficeHours.objects.filter(is_active=True).order_by('display_order', 'day')
    
    # Group office hours by day
    hours_by_day = {}
    for hours in office_hours:
        day = hours.get_day_display()
        if day not in hours_by_day:
            hours_by_day[day] = []
        hours_by_day[day].append(hours)
    
    context = {
        'contact_info_list': contact_info_list,
        'office_hours': office_hours,
        'hours_by_day': hours_by_day,
    }
    return render(request, "dashboard/contact.html", context)


@login_required
def home_view(request):
    """Home dashboard view with user-specific data and charts."""
    user = request.user
    
    # Get user dashboard statistics
    user_stats = get_user_dashboard_stats(user)
    
    # Get user-specific data
    upcoming_events = get_user_upcoming_events(user, limit=10)
    recent_activity = get_user_recent_activity(user, limit=10)
    news_feed = get_user_news_feed(user, limit=5)
    
    # Get past event registrations
    from apps.events.models import EventRegistration
    past_events = EventRegistration.objects.filter(
        user=user,
        event__end_date__lt=timezone.now()
    ).select_related("event", "event__category").order_by("-event__start_date")[:10]
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        user=user
    ).order_by("-created_at")[:10]
    
    # Prepare chart data for JavaScript (JSON serialized)
    event_chart_data = get_user_event_chart_data(user)
    payment_chart_data = get_user_payment_chart_data(user)
    event_status_data = get_user_event_status_chart_data(user)
    
    context = {
        "user": user,
        "user_stats": user_stats,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "recent_activity": recent_activity,
        "news_feed": news_feed,
        "recent_payments": recent_payments,
        # Chart data for JavaScript (JSON serialized)
        "event_chart_months": mark_safe(json.dumps(event_chart_data["months"])),
        "event_chart_counts": json.dumps(event_chart_data["counts"]),
        "payment_chart_months": mark_safe(json.dumps(payment_chart_data["months"])),
        "payment_chart_revenues": json.dumps(payment_chart_data["revenues"]),
        "event_status_labels": mark_safe(json.dumps(event_status_data["labels"])),
        "event_status_data": json.dumps(event_status_data["data"]),
    }
    
    return render(request, "dashboard/home.html", context)


def admin_or_board_check(user):
    """Check if user is admin or board member."""
    return user.is_authenticated and (user.is_admin() or user.is_board_member())


@login_required
@user_passes_test(admin_or_board_check)
def admin_dashboard_view(request):
    """Admin dashboard with analytics and metrics."""
    # Get date range from request
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    
    # Parse dates if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None
    if date_to:
        try:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None
    
    # Default to last 30 days if no date range provided
    if not date_from:
        date_from = timezone.now().date() - timedelta(days=30)
    if not date_to:
        date_to = timezone.now().date()
    
    # Get statistics
    member_stats = get_member_stats()
    recent_activity = get_recent_activity()
    event_stats = get_event_stats()
    revenue_stats = get_revenue_stats(
        date_from=date_from,
        date_to=date_to
    )
    
    # Get news statistics
    from apps.news.models import NewsPost
    total_news = NewsPost.objects.count()
    published_news = NewsPost.objects.filter(is_published=True).count()
    recent_news_count = NewsPost.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Prepare chart data for JavaScript (JSON serialized)
    # Convert lazy translation strings to regular strings for JSON serialization
    member_status_labels = [
        str(dict(Member.MembershipStatus.choices).get(status, status.title()))
        for status in member_stats["by_status"].keys()
    ]
    member_status_data = list(member_stats["by_status"].values())
    
    member_category_labels = [
        str(dict(Member.MemberCategory.choices).get(cat, cat.title()))
        for cat in member_stats["by_category"].keys()
    ]
    member_category_data = list(member_stats["by_category"].values())
    
    member_growth_months = [item["month"] for item in member_stats["monthly_growth"]]
    member_growth_data = [item["count"] for item in member_stats["monthly_growth"]]
    
    revenue_months = [item["month"] for item in revenue_stats["monthly_revenue"]]
    revenue_data = [float(item["revenue"]) for item in revenue_stats["monthly_revenue"]]
    
    revenue_type_labels = [
        str(dict(Payment.PaymentType.choices).get(item["type"], item["type"].title()))
        for item in revenue_stats["by_type"]
    ]
    revenue_type_data = [float(item["total"]) for item in revenue_stats["by_type"]]
    
    context = {
        "member_stats": member_stats,
        "recent_activity": recent_activity,
        "event_stats": event_stats,
        "revenue_stats": revenue_stats,
        "news_stats": {
            "total": total_news,
            "published": published_news,
            "recent": recent_news_count,
        },
        "date_from": date_from,
        "date_to": date_to,
        # Chart data for JavaScript (JSON serialized)
        "member_status_labels": mark_safe(json.dumps(member_status_labels)),
        "member_status_data": json.dumps(member_status_data),
        "member_category_labels": mark_safe(json.dumps(member_category_labels)),
        "member_category_data": json.dumps(member_category_data),
        "member_growth_months": mark_safe(json.dumps(member_growth_months)),
        "member_growth_data": json.dumps(member_growth_data),
        "revenue_months": mark_safe(json.dumps(revenue_months)),
        "revenue_data": json.dumps(revenue_data),
        "revenue_type_labels": mark_safe(json.dumps(revenue_type_labels)),
        "revenue_type_data": json.dumps(revenue_type_data),
    }
    
    return render(request, "dashboard/admin.html", context)


@login_required
@user_passes_test(admin_or_board_check)
def export_report_view(request):
    """Export custom reports as CSV."""
    report_type = request.GET.get("type", "members")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    
    # Parse dates if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None
    if date_to:
        try:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None
    
    # Generate report data
    data = generate_report_data(
        report_type=report_type,
        date_from=date_from,
        date_to=date_to
    )
    
    if not data:
        return HttpResponse("No data to export", status=404)
    
    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    filename = f"{report_type}_report_{timezone.now().strftime('%Y%m%d')}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    
    # Write CSV
    writer = csv.DictWriter(response, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return response


@login_required
@user_passes_test(admin_or_board_check)
def admin_dashboard_api_view(request):
    """JSON API endpoint for real-time admin dashboard data."""
    # Get date range from request
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    
    # Parse dates if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None
    if date_to:
        try:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None
    
    # Default to last 30 days if no date range provided
    if not date_from:
        date_from = timezone.now().date() - timedelta(days=30)
    if not date_to:
        date_to = timezone.now().date()
    
    # Get statistics - fetch fresh data each time
    member_stats = get_member_stats()
    recent_activity = get_recent_activity()
    event_stats = get_event_stats()
    revenue_stats = get_revenue_stats(
        date_from=date_from,
        date_to=date_to
    )
    
    # Get news statistics
    from apps.news.models import NewsPost
    total_news = NewsPost.objects.count()
    published_news = NewsPost.objects.filter(is_published=True).count()
    recent_news_count = NewsPost.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Serialize data for JSON response
    # Convert QuerySets and objects to dictionaries
    recent_members_data = []
    for member in recent_activity["recent_members"]:
        recent_members_data.append({
            "name": member.user.full_name,
            "status": str(member.get_status_display()),
            "joined_date": member.joined_date.strftime("%Y-%m-%d") if member.joined_date else None,
        })
    
    recent_news_data = []
    for news in recent_activity["recent_news"]:
        recent_news_data.append({
            "title": news.title,
            "author": news.author.full_name,
            "created_at": news.created_at.strftime("%Y-%m-%d") if news.created_at else None,
        })
    
    # Event registrations
    recent_event_registrations_data = []
    for reg in recent_activity["recent_event_registrations"]:
        recent_event_registrations_data.append({
            "user_name": reg.user.full_name,
            "event_title": reg.event.title,
            "status": str(reg.get_status_display()),
            "registered_at": reg.registered_at.strftime("%Y-%m-%d %H:%M") if reg.registered_at else None,
        })
    
    # Recent events created
    recent_events_data = []
    for event in recent_activity["recent_events"]:
        recent_events_data.append({
            "title": event.title,
            "organizer": event.organizer.full_name if event.organizer else None,
            "start_date": event.start_date.strftime("%Y-%m-%d") if event.start_date else None,
            "created_at": event.created_at.strftime("%Y-%m-%d") if event.created_at else None,
        })
    
    # Forum posts (already in dict format)
    recent_forum_posts_data = recent_activity.get("recent_forum_posts", [])
    for post in recent_forum_posts_data:
        if isinstance(post.get("date"), datetime):
            post["date"] = post["date"].strftime("%Y-%m-%d %H:%M")
    
    # Documents
    recent_documents_data = []
    for doc in recent_activity.get("recent_documents", []):
        recent_documents_data.append({
            "title": doc.title,
            "uploader": doc.uploader.full_name if doc.uploader else None,
            "created_at": doc.created_at.strftime("%Y-%m-%d") if doc.created_at else None,
        })
    
    # Recent payments for activity section (from recent_activity, not revenue_stats)
    recent_payments_activity_data = []
    for payment in recent_activity.get("recent_payments", []):
        recent_payments_activity_data.append({
            "user_name": payment.user.full_name,
            "amount": float(payment.amount),
            "status": str(payment.get_status_display()),
            "created_at": payment.created_at.strftime("%Y-%m-%d") if payment.created_at else None,
        })
    
    upcoming_events_data = []
    for event in event_stats["upcoming_list"]:
        upcoming_events_data.append({
            "title": event.title,
            "start_date": event.start_date.strftime("%Y-%m-%d") if event.start_date else None,
            "location": event.location or "TBA",
        })
    
    popular_events_data = []
    for event in event_stats["popular_events"]:
        popular_events_data.append({
            "title": event.title,
            "registration_count": event.registration_count,
        })
    
    recent_payments_data = []
    for payment in revenue_stats["recent_payments"]:
        recent_payments_data.append({
            "user_name": payment.user.full_name,
            "amount": float(payment.amount),
            "status": str(payment.get_status_display()),
            "created_at": payment.created_at.strftime("%Y-%m-%d") if payment.created_at else None,
        })
    
    # Prepare chart data
    # Convert lazy translation strings to regular strings for JSON serialization
    member_status_labels = [
        str(dict(Member.MembershipStatus.choices).get(status, status.title()))
        for status in member_stats["by_status"].keys()
    ]
    member_status_data = list(member_stats["by_status"].values())
    
    member_category_labels = [
        str(dict(Member.MemberCategory.choices).get(cat, cat.title()))
        for cat in member_stats["by_category"].keys()
    ]
    member_category_data = list(member_stats["by_category"].values())
    
    member_growth_months = [item["month"] for item in member_stats["monthly_growth"]]
    member_growth_data = [item["count"] for item in member_stats["monthly_growth"]]
    
    revenue_months = [item["month"] for item in revenue_stats["monthly_revenue"]]
    revenue_data = [float(item["revenue"]) for item in revenue_stats["monthly_revenue"]]
    
    revenue_type_labels = [
        str(dict(Payment.PaymentType.choices).get(item["type"], item["type"].title()))
        for item in revenue_stats["by_type"]
    ]
    revenue_type_data = [float(item["total"]) for item in revenue_stats["by_type"]]
    
    response_data = {
        "member_stats": {
            "total": member_stats["total"],
            "active": member_stats["active"],
            "inactive": member_stats["inactive"],
            "pending": member_stats["pending"],
            "suspended": member_stats["suspended"],
            "recent_registrations": member_stats["recent_registrations"],
            "by_status": member_stats["by_status"],
            "by_category": member_stats["by_category"],
        },
        "event_stats": {
            "total": event_stats["total"],
            "upcoming": event_stats["upcoming"],
            "past": event_stats["past"],
            "total_registrations": event_stats["total_registrations"],
            "attendance_rate": event_stats["attendance_rate"],
            "upcoming_list": upcoming_events_data,
            "popular_events": popular_events_data,
        },
        "revenue_stats": {
            "total_revenue": float(revenue_stats["total_revenue"]),
            "recent_payments": recent_payments_data,
        },
        "news_stats": {
            "total": total_news,
            "published": published_news,
            "recent": recent_news_count,
        },
        "recent_activity": {
            "recent_members": recent_members_data,
            "recent_news": recent_news_data,
            "recent_event_registrations": recent_event_registrations_data,
            "recent_events": recent_events_data,
            "recent_payments": recent_payments_activity_data,
            "recent_forum_posts": recent_forum_posts_data,
            "recent_documents": recent_documents_data,
        },
        "chart_data": {
            "member_status_labels": member_status_labels,
            "member_status_data": member_status_data,
            "member_category_labels": member_category_labels,
            "member_category_data": member_category_data,
            "member_growth_months": member_growth_months,
            "member_growth_data": member_growth_data,
            "revenue_months": revenue_months,
            "revenue_data": revenue_data,
            "revenue_type_labels": revenue_type_labels,
            "revenue_type_data": revenue_type_data,
        },
        "timestamp": timezone.now().isoformat(),
    }
    
    return JsonResponse(response_data)


def health_check_view(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 if critical services (database) are healthy.
    Redis and cache failures are reported but don't fail the health check.
    """
    from django.db import connection
    from django.conf import settings
    import redis
    import logging
    
    logger = logging.getLogger(__name__)
    status = {
        'status': 'healthy',
        'checks': {},
        'timestamp': timezone.now().isoformat(),
    }
    
    critical_failed = False
    
    # Database check (CRITICAL - must pass)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        critical_failed = True
        logger.error(f"Health check: Database error - {str(e)}")
    
    # Redis check (NON-CRITICAL - report but don't fail)
    try:
        redis_url = getattr(settings, 'REDIS_URL', 'redis://127.0.0.1:6379/0')
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        status['checks']['redis'] = 'ok'
    except Exception as e:
        status['checks']['redis'] = f'error: {str(e)}'
        # Redis failure is non-critical - app can work without it (with degraded functionality)
        logger.warning(f"Health check: Redis error - {str(e)}")
    
    # Cache check (NON-CRITICAL - report but don't fail)
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            status['checks']['cache'] = 'ok'
        else:
            status['checks']['cache'] = 'error: cache test failed'
            logger.warning("Health check: Cache test failed")
    except Exception as e:
        status['checks']['cache'] = f'error: {str(e)}'
        # Cache failure is non-critical
        logger.warning(f"Health check: Cache error - {str(e)}")
    
    # Return 200 if database is healthy (critical), 503 only if database fails
    http_status = 503 if critical_failed else 200
    return JsonResponse(status, status=http_status)

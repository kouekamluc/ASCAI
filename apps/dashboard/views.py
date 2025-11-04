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
    context = {}
    return render(request, "dashboard/index.html", context)


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
    member_status_labels = [
        dict(Member.MembershipStatus.choices).get(status, status.title())
        for status in member_stats["by_status"].keys()
    ]
    member_status_data = list(member_stats["by_status"].values())
    
    member_category_labels = [
        dict(Member.MemberCategory.choices).get(cat, cat.title())
        for cat in member_stats["by_category"].keys()
    ]
    member_category_data = list(member_stats["by_category"].values())
    
    member_growth_months = [item["month"] for item in member_stats["monthly_growth"]]
    member_growth_data = [item["count"] for item in member_stats["monthly_growth"]]
    
    revenue_months = [item["month"] for item in revenue_stats["monthly_revenue"]]
    revenue_data = [float(item["revenue"]) for item in revenue_stats["monthly_revenue"]]
    
    revenue_type_labels = [
        dict(Payment.PaymentType.choices).get(item["type"], item["type"].title())
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
            "status": member.get_status_display(),
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
            "status": reg.get_status_display(),
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
            "status": payment.get_status_display(),
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
            "status": payment.get_status_display(),
            "created_at": payment.created_at.strftime("%Y-%m-%d") if payment.created_at else None,
        })
    
    # Prepare chart data
    member_status_labels = [
        dict(Member.MembershipStatus.choices).get(status, status.title())
        for status in member_stats["by_status"].keys()
    ]
    member_status_data = list(member_stats["by_status"].values())
    
    member_category_labels = [
        dict(Member.MemberCategory.choices).get(cat, cat.title())
        for cat in member_stats["by_category"].keys()
    ]
    member_category_data = list(member_stats["by_category"].values())
    
    member_growth_months = [item["month"] for item in member_stats["monthly_growth"]]
    member_growth_data = [item["count"] for item in member_stats["monthly_growth"]]
    
    revenue_months = [item["month"] for item in revenue_stats["monthly_revenue"]]
    revenue_data = [float(item["revenue"]) for item in revenue_stats["monthly_revenue"]]
    
    revenue_type_labels = [
        dict(Payment.PaymentType.choices).get(item["type"], item["type"].title())
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

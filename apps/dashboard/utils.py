"""
Dashboard utilities for analytics and reporting.
"""

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict

from apps.members.models import Member
from apps.news.models import NewsPost
from apps.events.models import Event, EventRegistration
from apps.accounts.models import User
from .models import Payment


def get_member_stats():
    """Get comprehensive member statistics."""
    # Count total members: Users with Member profiles OR users with member/board/admin roles
    # This ensures we count all registered members, even if they don't have profiles yet
    users_with_profiles = set(Member.objects.values_list('user_id', flat=True))
    users_with_member_roles = User.objects.filter(
        role__in=[User.Role.MEMBER, User.Role.BOARD, User.Role.ADMIN]
    ).exclude(id__in=users_with_profiles).count()
    
    # Total = members with profiles + users with member roles (but no profile)
    total_members = Member.objects.count() + users_with_member_roles
    
    # Status counts - only from Member profiles (users without profiles are considered pending)
    active_members = Member.objects.filter(
        status=Member.MembershipStatus.ACTIVE
    ).count()
    inactive_members = Member.objects.filter(
        status=Member.MembershipStatus.INACTIVE
    ).count()
    pending_members = Member.objects.filter(
        status=Member.MembershipStatus.PENDING
    ).count() + users_with_member_roles  # Include users without profiles as pending
    suspended_members = Member.objects.filter(
        status=Member.MembershipStatus.SUSPENDED
    ).count()
    
    # By category
    by_category = Member.objects.values("category").annotate(
        count=Count("id")
    ).order_by("-count")
    category_stats = {
        item["category"]: item["count"] 
        for item in by_category
    }
    
    # By status
    by_status = Member.objects.values("status").annotate(
        count=Count("id")
    ).order_by("-count")
    status_stats = {
        item["status"]: item["count"] 
        for item in by_status
    }
    
    # Recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_registrations = Member.objects.filter(
        joined_date__gte=thirty_days_ago
    ).count()
    
    # Monthly growth (last 6 months)
    monthly_growth = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        count = Member.objects.filter(
            joined_date__gte=month_start,
            joined_date__lt=month_end
        ).count()
        monthly_growth.insert(0, {
            "month": month_start.strftime("%Y-%m"),
            "count": count
        })
    
    return {
        "total": total_members,
        "active": active_members,
        "inactive": inactive_members,
        "pending": pending_members,
        "suspended": suspended_members,
        "by_category": category_stats,
        "by_status": status_stats,
        "recent_registrations": recent_registrations,
        "monthly_growth": monthly_growth,
    }


def get_recent_activity():
    """Get recent activity across the platform."""
    # Recent member registrations (last 10)
    recent_members = Member.objects.select_related("user").order_by(
        "-joined_date"
    )[:10]
    
    # Recent news posts (last 10)
    recent_news = NewsPost.objects.select_related("author").filter(
        is_published=True
    ).order_by("-published_at", "-created_at")[:10]
    
    # Recent event registrations (last 10)
    from apps.events.models import EventRegistration
    recent_event_registrations = EventRegistration.objects.select_related(
        "user", "event"
    ).order_by("-registered_at")[:10]
    
    # Recent events created (last 10)
    recent_events = Event.objects.select_related("organizer", "category").order_by(
        "-created_at"
    )[:10]
    
    # Recent payments (last 10)
    recent_payments = Payment.objects.select_related("user").order_by(
        "-created_at"
    )[:10]
    
    # Recent forum activity (if forums app exists)
    recent_forum_posts = []
    try:
        from apps.forums.models import Thread, Reply
        # Recent forum threads
        recent_threads = Thread.objects.select_related("author", "category").order_by(
            "-created_at"
        )[:5]
        for thread in recent_threads:
            recent_forum_posts.append({
                "type": "thread",
                "title": thread.title,
                "author": thread.author.full_name,
                "date": thread.created_at,
                "category": thread.category.name if thread.category else None,
            })
        
        # Recent forum replies
        recent_replies = Reply.objects.select_related("author", "thread").order_by(
            "-created_at"
        )[:5]
        for reply in recent_replies:
            recent_forum_posts.append({
                "type": "reply",
                "title": f"Reply to: {reply.thread.title}",
                "author": reply.author.full_name,
                "date": reply.created_at,
                "category": reply.thread.category.name if reply.thread.category else None,
            })
        
        # Sort forum posts by date
        recent_forum_posts.sort(key=lambda x: x["date"], reverse=True)
        recent_forum_posts = recent_forum_posts[:10]
    except ImportError:
        pass
    
    # Recent document uploads (if documents app exists)
    recent_documents = []
    try:
        from apps.documents.models import Document
        recent_docs = Document.objects.select_related("uploader").order_by(
            "-created_at"
        )[:10]
        for doc in recent_docs:
            recent_documents.append(doc)
    except ImportError:
        pass
    
    return {
        "recent_members": recent_members,
        "recent_news": recent_news,
        "recent_event_registrations": recent_event_registrations,
        "recent_events": recent_events,
        "recent_payments": recent_payments,
        "recent_forum_posts": recent_forum_posts,
        "recent_documents": recent_documents,
    }


def get_event_stats():
    """Get event analytics statistics."""
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(
        start_date__gte=timezone.now()
    ).count()
    past_events = Event.objects.filter(
        start_date__lt=timezone.now()
    ).count()
    
    # Events by category (category is a ForeignKey to EventCategory)
    by_category = Event.objects.values("category__name").annotate(
        count=Count("id")
    ).order_by("-count")
    category_stats = {
        item["category__name"]: item["count"] 
        for item in by_category
        if item["category__name"] is not None
    }
    
    # Upcoming events (next 10)
    upcoming_list = Event.objects.filter(
        start_date__gte=timezone.now()
    ).order_by("start_date")[:10]
    
    # Most popular events (by registration count)
    popular_events = Event.objects.annotate(
        registration_count=Count("registrations")
    ).order_by("-registration_count")[:5]
    
    # Total registrations
    total_registrations = EventRegistration.objects.count()
    attended_registrations = EventRegistration.objects.filter(
        status=EventRegistration.Status.ATTENDED
    ).count()
    
    # Average attendance rate
    attendance_rate = 0
    if total_registrations > 0:
        attendance_rate = round(
            (attended_registrations / total_registrations) * 100, 1
        )
    
    return {
        "total": total_events,
        "upcoming": upcoming_events,
        "past": past_events,
        "by_category": category_stats,
        "upcoming_list": upcoming_list,
        "popular_events": popular_events,
        "total_registrations": total_registrations,
        "attended_registrations": attended_registrations,
        "attendance_rate": attendance_rate,
    }


def get_revenue_stats(date_from=None, date_to=None):
    """Get revenue tracking statistics."""
    # Build date filter
    payment_filter = Q()
    if date_from:
        payment_filter &= Q(created_at__gte=date_from)
    if date_to:
        payment_filter &= Q(created_at__lte=date_to)
    
    # Total revenue (completed payments only)
    total_revenue = Payment.objects.filter(
        payment_filter,
        status=Payment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or 0
    
    # By payment type
    by_type = Payment.objects.filter(
        payment_filter,
        status=Payment.PaymentStatus.COMPLETED
    ).values("payment_type").annotate(
        total=Sum("amount"),
        count=Count("id")
    ).order_by("-total")
    type_stats = [
        {
            "type": item["payment_type"],
            "total": float(item["total"]),
            "count": item["count"]
        }
        for item in by_type
    ]
    
    # By status
    by_status = Payment.objects.filter(
        payment_filter
    ).values("status").annotate(
        total=Sum("amount"),
        count=Count("id")
    ).order_by("-total")
    status_stats = [
        {
            "status": item["status"],
            "total": float(item["total"] or 0),
            "count": item["count"]
        }
        for item in by_status
    ]
    
    # Monthly breakdown (last 12 months)
    monthly_revenue = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        revenue = Payment.objects.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status=Payment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"] or 0
        monthly_revenue.insert(0, {
            "month": month_start.strftime("%Y-%m"),
            "revenue": float(revenue)
        })
    
    # Recent payments (last 10)
    recent_payments = Payment.objects.filter(
        payment_filter
    ).select_related("user").order_by("-created_at")[:10]
    
    return {
        "total_revenue": float(total_revenue),
        "by_type": type_stats,
        "by_status": status_stats,
        "monthly_revenue": monthly_revenue,
        "recent_payments": recent_payments,
    }


def generate_report_data(report_type, date_from=None, date_to=None):
    """Generate data for custom reports (CSV export)."""
    if report_type == "members":
        members = Member.objects.select_related("user").all()
        if date_from:
            members = members.filter(joined_date__gte=date_from)
        if date_to:
            members = members.filter(joined_date__lte=date_to)
        
        return [
            {
                "Membership Number": member.membership_number or "",
                "Name": member.user.full_name,
                "Email": member.user.email,
                "Status": member.get_status_display(),
                "Category": member.get_category_display(),
                "University": member.university or "",
                "Course": member.course or "",
                "Joined Date": member.joined_date.strftime("%Y-%m-%d") if member.joined_date else "",
            }
            for member in members
        ]
    
    elif report_type == "events":
        events = Event.objects.select_related("organizer", "category").all()
        if date_from:
            events = events.filter(start_date__gte=date_from)
        if date_to:
            events = events.filter(start_date__lte=date_to)
        
        return [
            {
                "Title": event.title,
                "Start Date": event.start_date.strftime("%Y-%m-%d %H:%M") if event.start_date else "",
                "End Date": event.end_date.strftime("%Y-%m-%d %H:%M") if event.end_date else "",
                "Location": event.location or "",
                "Category": event.category.name if event.category else "",
                "Capacity": event.max_attendees or "",
                "Registrations": event.registrations.count(),
                "Organizer": event.organizer.full_name if event.organizer else "",
            }
            for event in events
        ]
    
    elif report_type == "revenue":
        payments = Payment.objects.select_related("user").all()
        if date_from:
            payments = payments.filter(created_at__gte=date_from)
        if date_to:
            payments = payments.filter(created_at__lte=date_to)
        
        return [
            {
                "User": payment.user.full_name,
                "Email": payment.user.email,
                "Amount": str(payment.amount),
                "Payment Type": payment.get_payment_type_display(),
                "Status": payment.get_status_display(),
                "Transaction ID": payment.transaction_id or "",
                "Paid At": payment.paid_at.strftime("%Y-%m-%d %H:%M") if payment.paid_at else "",
                "Created At": payment.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for payment in payments
        ]
    
    return []


def get_user_dashboard_stats(user):
    """Get user-specific statistics for dashboard."""
    # Get user's member profile if exists
    member_profile = None
    try:
        member_profile = user.member_profile
    except Member.DoesNotExist:
        pass
    
    # Event registrations stats
    event_registrations = EventRegistration.objects.filter(user=user)
    total_registered = event_registrations.count()
    upcoming_count = event_registrations.filter(
        event__start_date__gte=timezone.now(),
        status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.WAITLISTED]
    ).count()
    attended_count = event_registrations.filter(
        status=EventRegistration.Status.ATTENDED
    ).count()
    past_registrations = event_registrations.filter(
        event__end_date__lt=timezone.now()
    ).count()
    
    # Payment stats
    payments = Payment.objects.filter(user=user)
    total_payments = payments.filter(status=Payment.PaymentStatus.COMPLETED).count()
    total_paid = payments.filter(
        status=Payment.PaymentStatus.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or 0
    
    # Job applications stats
    job_applications_count = 0
    try:
        from apps.jobs.models import JobApplication
        job_applications_count = JobApplication.objects.filter(applicant=user).count()
    except ImportError:
        pass
    
    # Documents uploaded count
    documents_count = 0
    try:
        from apps.documents.models import Document
        documents_count = Document.objects.filter(uploader=user).count()
    except ImportError:
        pass
    
    return {
        "member_profile": member_profile,
        "total_events_registered": total_registered,
        "upcoming_events": upcoming_count,
        "events_attended": attended_count,
        "past_events": past_registrations,
        "total_payments": total_payments,
        "total_paid": float(total_paid),
    }


def get_user_upcoming_events(user, limit=10):
    """Get user's upcoming event registrations."""
    return EventRegistration.objects.filter(
        user=user,
        event__start_date__gte=timezone.now(),
        status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.WAITLISTED]
    ).select_related("event", "event__category").order_by("event__start_date")[:limit]


def get_user_recent_activity(user, limit=10):
    """Get user's recent activity (registrations, payments, etc.)."""
    activities = []
    
    # Recent event registrations
    recent_registrations = EventRegistration.objects.filter(
        user=user
    ).select_related("event").order_by("-registered_at")[:5]
    
    for reg in recent_registrations:
        activities.append({
            "type": "event_registration",
            "title": f"Registered for {reg.event.title}",
            "date": reg.registered_at,
            "status": reg.get_status_display(),
            "url": reg.event.get_absolute_url() if hasattr(reg.event, 'get_absolute_url') else None,
        })
    
    # Recent payments
    recent_payments = Payment.objects.filter(
        user=user
    ).order_by("-created_at")[:5]
    
    for payment in recent_payments:
        activities.append({
            "type": "payment",
            "title": f"Payment: {payment.get_payment_type_display()} - €{payment.amount}",
            "date": payment.created_at,
            "status": payment.get_status_display(),
            "url": None,
        })
    
    # Recent document uploads
    try:
        from apps.documents.models import Document
        recent_docs = Document.objects.filter(
            uploader=user
        ).order_by("-created_at")[:3]
        
        for doc in recent_docs:
            activities.append({
                "type": "document_upload",
                "title": f"Uploaded document: {doc.title}",
                "date": doc.created_at,
                "status": "Uploaded",
                "url": doc.get_absolute_url() if hasattr(doc, 'get_absolute_url') else None,
            })
    except ImportError:
        pass
    
    # Sort by date descending
    activities.sort(key=lambda x: x["date"], reverse=True)
    
    return activities[:limit]


def get_user_news_feed(user, limit=5):
    """Get relevant news posts for the user."""
    news_posts = NewsPost.objects.filter(
        is_published=True
    ).select_related("author", "category").order_by("-published_at", "-created_at")
    
    # Filter by visibility
    accessible_posts = []
    for post in news_posts:
        if post.can_view(user):
            accessible_posts.append(post)
            if len(accessible_posts) >= limit:
                break
    
    return accessible_posts


def get_user_event_chart_data(user):
    """Prepare chart data for user's event participation over time."""
    # Get registrations grouped by month (last 12 months)
    monthly_data = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        count = EventRegistration.objects.filter(
            user=user,
            registered_at__gte=month_start,
            registered_at__lt=month_end
        ).count()
        
        monthly_data.insert(0, {
            "month": month_start.strftime("%Y-%m"),
            "count": count
        })
    
    months = [item["month"] for item in monthly_data]
    counts = [item["count"] for item in monthly_data]
    
    return {
        "months": months,
        "counts": counts,
    }


def get_user_payment_chart_data(user):
    """Prepare chart data for user's payment history."""
    # Get payments grouped by month (last 12 months)
    monthly_data = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        revenue = Payment.objects.filter(
            user=user,
            created_at__gte=month_start,
            created_at__lt=month_end,
            status=Payment.PaymentStatus.COMPLETED
        ).aggregate(total=Sum("amount"))["total"] or 0
        
        monthly_data.insert(0, {
            "month": month_start.strftime("%Y-%m"),
            "revenue": float(revenue)
        })
    
    months = [item["month"] for item in monthly_data]
    revenues = [item["revenue"] for item in monthly_data]
    
    return {
        "months": months,
        "revenues": revenues,
    }


def get_user_event_status_chart_data(user):
    """Prepare chart data for user's event registration status distribution."""
    # Get counts by status
    status_counts = EventRegistration.objects.filter(
        user=user
    ).values("status").annotate(count=Count("id"))
    
    status_dict = {
        EventRegistration.Status.REGISTERED: 0,
        EventRegistration.Status.WAITLISTED: 0,
        EventRegistration.Status.ATTENDED: 0,
        EventRegistration.Status.CANCELLED: 0,
    }
    
    for item in status_counts:
        status_dict[item["status"]] = item["count"]
    
    labels = [
        str(dict(EventRegistration.Status.choices).get(status, status.title()))
        for status in status_dict.keys()
    ]
    data = list(status_dict.values())
    
    return {
        "labels": labels,
        "data": data,
    }
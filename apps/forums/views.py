"""
Views for forums app.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from functools import wraps

from .models import Category, Thread, Reply, Vote, Flag, Notification, ModeratorAction, UserBan
from .forms import ThreadForm, ReplyForm, FlagForm
from .mixins import ModeratorRequiredMixin, MemberRequiredMixin, NotBannedMixin, AuthorOrModeratorRequiredMixin


def moderator_required(view_func):
    """Decorator to require moderator permissions."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to perform this action."))
            return redirect("accounts:login")
        if not (request.user.is_admin() or request.user.is_board_member()):
            messages.error(request, _("You do not have permission to perform this action."))
            return redirect("forums:category_list")
        return view_func(request, *args, **kwargs)
    return wrapper


def not_banned(view_func):
    """Decorator to prevent banned users from posting."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            active_ban = UserBan.objects.filter(user=request.user, is_active=True).first()
            if active_ban and active_ban.is_currently_active():
                messages.error(request, _("You are banned from posting. Reason: %(reason)s") % {"reason": active_ban.reason})
                return redirect("forums:category_list")
        return view_func(request, *args, **kwargs)
    return wrapper


def category_list(request):
    """List all forum categories."""
    # Get all active categories
    categories = Category.objects.filter(is_active=True)
    
    # Filter categories by view permissions
    accessible_categories = []
    for category in categories:
        if category.can_user_view(request.user):
            # Annotate thread count for each accessible category
            category.thread_count = category.get_thread_count()
            accessible_categories.append(category)
    
    context = {
        "categories": accessible_categories,
    }
    
    return render(request, "forums/category_list.html", context)


def category_detail(request, slug):
    """Show threads in a category."""
    category = get_object_or_404(Category, slug=slug)
    
    # Check if user can view this category
    if not category.can_user_view(request.user):
        messages.error(request, _("You don't have permission to view this category."))
        return redirect("forums:category_list")
    
    # Get threads
    threads = Thread.objects.filter(category=category, is_approved=True)
    
    # Filter by pinned/unpinned
    sort_by = request.GET.get("sort", "recent")
    if sort_by == "oldest":
        threads = threads.order_by("created_at")
    elif sort_by == "most_replies":
        threads = threads.order_by("-reply_count", "-last_activity")
    else:  # recent (default)
        threads = threads.order_by("-is_pinned", "-last_activity")
    
    # Pagination
    paginator = Paginator(threads, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "category": category,
        "page_obj": page_obj,
        "sort_by": sort_by,
        "can_post": category.can_user_post(request.user),
    }
    
    return render(request, "forums/category_detail.html", context)


def thread_detail(request, slug):
    """Show thread with replies."""
    thread = get_object_or_404(Thread, slug=slug)
    
    # Check if user can view this thread's category
    if not thread.category.can_user_view(request.user):
        messages.error(request, _("You don't have permission to view this thread."))
        return redirect("forums:category_list")
    
    # Increment view count
    thread.increment_view_count()
    
    # Get replies
    replies = thread.replies.filter(is_approved=True).select_related("author")
    
    # Pagination
    paginator = Paginator(replies, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get vote information
    thread_content_type = ContentType.objects.get_for_model(Thread)
    thread_votes = Vote.objects.filter(
        content_type=thread_content_type,
        object_id=thread.pk
    )
    thread_upvotes = thread_votes.filter(vote_type=Vote.VoteType.UPVOTE).count()
    thread_downvotes = thread_votes.filter(vote_type=Vote.VoteType.DOWNVOTE).count()
    thread_vote_score = thread_upvotes - thread_downvotes
    
    # Get user's vote for thread
    user_thread_vote = None
    if request.user.is_authenticated:
        user_thread_vote = thread_votes.filter(user=request.user).first()
    
    # Get votes for replies - prepare structured data
    reply_content_type = ContentType.objects.get_for_model(Reply)
    reply_ids = [reply.pk for reply in page_obj]
    reply_vote_data = {}
    
    if reply_ids:
        votes = Vote.objects.filter(
            content_type=reply_content_type,
            object_id__in=reply_ids
        ).select_related("user")
        
        for reply in page_obj:
            reply_vote_objs = votes.filter(object_id=reply.pk)
            upvotes = reply_vote_objs.filter(vote_type=Vote.VoteType.UPVOTE).count()
            downvotes = reply_vote_objs.filter(vote_type=Vote.VoteType.DOWNVOTE).count()
            score = upvotes - downvotes
            
            user_vote = None
            if request.user.is_authenticated:
                user_vote = reply_vote_objs.filter(user=request.user).first()
            
            reply_vote_data[reply.pk] = {
                "score": score,
                "user_vote": user_vote,
            }
    
    context = {
        "thread": thread,
        "page_obj": page_obj,
        "reply_form": ReplyForm(),
        "thread_vote_score": thread_vote_score,
        "user_thread_vote": user_thread_vote,
        "thread_content_type_id": thread_content_type.pk,
        "reply_content_type_id": reply_content_type.pk,
        "reply_vote_data": reply_vote_data,
    }
    
    return render(request, "forums/thread_detail.html", context)


@login_required
@not_banned
def thread_create(request, slug):
    """Create a new thread."""
    category = get_object_or_404(Category, slug=slug)
    
    # Check if user can post in this category
    if not category.can_user_post(request.user):
        messages.error(request, _("You don't have permission to post in this category."))
        return redirect("forums:category_detail", slug=category.slug)
    
    if request.method == "POST":
        form = ThreadForm(request.POST, user=request.user)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.category = category
            thread.slug = slugify(thread.title)
            
            # Check if slug is unique, if not append number
            original_slug = thread.slug
            counter = 1
            while Thread.objects.filter(slug=thread.slug).exists():
                thread.slug = f"{original_slug}-{counter}"
                counter += 1
            
            thread.save()
            messages.success(request, _("Thread created successfully."))
            
            # Create approval notification if first post
            if not request.user.is_member():
                messages.info(request, _("Your thread is pending approval."))
            
            return redirect("forums:thread_detail", slug=thread.slug)
    else:
        form = ThreadForm(user=request.user)
    
    context = {
        "form": form,
        "category": category,
    }
    
    return render(request, "forums/thread_form.html", context)


@login_required
@not_banned
def thread_update(request, slug):
    """Edit an existing thread."""
    thread = get_object_or_404(Thread, slug=slug)
    
    # Check if user is author or moderator
    if thread.author != request.user and not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("You don't have permission to edit this thread."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    if request.method == "POST":
        form = ThreadForm(request.POST, instance=thread, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Thread updated successfully."))
            return redirect("forums:thread_detail", slug=thread.slug)
    else:
        form = ThreadForm(instance=thread, user=request.user)
    
    context = {
        "form": form,
        "thread": thread,
    }
    
    return render(request, "forums/thread_form.html", context)


@login_required
def thread_delete(request, slug):
    """Delete a thread."""
    thread = get_object_or_404(Thread, slug=slug)
    
    # Check if user is author or moderator
    if thread.author != request.user and not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("You don't have permission to delete this thread."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    if request.method == "POST":
        category_slug = thread.category.slug
        thread.delete()
        messages.success(request, _("Thread deleted successfully."))
        return redirect("forums:category_detail", slug=category_slug)
    
    context = {
        "thread": thread,
    }
    
    return render(request, "forums/thread_confirm_delete.html", context)


@login_required
@not_banned
def reply_create(request, slug):
    """Create a reply to a thread."""
    thread = get_object_or_404(Thread, slug=slug)
    
    # Check if thread is locked
    if thread.is_locked and not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("This thread is locked."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    if request.method == "POST":
        form = ReplyForm(request.POST, thread=thread)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.thread = thread
            
            # Set approved status based on user role
            if not request.user.is_member():
                reply.is_approved = False
                messages.info(request, _("Your reply is pending approval."))
            
            reply.save()
            messages.success(request, _("Reply posted successfully."))
            
            # Broadcast real-time update
            try:
                from .utils import broadcast_reply_update
                broadcast_reply_update(reply, thread)
            except Exception:
                pass  # Fail silently if channels not available
            
            # Check if HTMX request for dynamic update
            if request.htmx:
                # Get content type for voting
                reply_content_type = ContentType.objects.get_for_model(Reply)
                context = {
                    "reply": reply,
                    "user": request.user,
                    "reply_content_type_id": reply_content_type.pk,
                    "reply_vote_data": {reply.pk: {"score": 0, "user_vote": None}},
                }
                return render(request, "forums/partials/reply_item.html", context)
            
            return redirect("forums:thread_detail", slug=thread.slug)
    else:
        form = ReplyForm(thread=thread)
    
    context = {
        "form": form,
        "thread": thread,
    }
    
    return render(request, "forums/reply_form.html", context)


@login_required
@not_banned
def reply_update(request, slug, reply_id):
    """Edit a reply."""
    thread = get_object_or_404(Thread, slug=slug)
    reply = get_object_or_404(Reply, pk=reply_id, thread=thread)
    
    # Check if user is author or moderator
    if reply.author != request.user and not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("You don't have permission to edit this reply."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    if request.method == "POST":
        form = ReplyForm(request.POST, instance=reply, thread=thread)
        if form.is_valid():
            form.save()
            messages.success(request, _("Reply updated successfully."))
            
            if request.htmx:
                return render(request, "forums/partials/reply_item.html", {"reply": reply})
            
            return redirect("forums:thread_detail", slug=thread.slug)
    else:
        form = ReplyForm(instance=reply, thread=thread)
    
    context = {
        "form": form,
        "reply": reply,
        "thread": thread,
    }
    
    return render(request, "forums/reply_form.html", context)


@login_required
def reply_delete(request, slug, reply_id):
    """Delete a reply."""
    thread = get_object_or_404(Thread, slug=slug)
    reply = get_object_or_404(Reply, pk=reply_id, thread=thread)
    
    # Check if user is author or moderator
    if reply.author != request.user and not (request.user.is_admin() or request.user.is_board_member()):
        messages.error(request, _("You don't have permission to delete this reply."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    if request.method == "POST":
        reply.delete()
        messages.success(request, _("Reply deleted successfully."))
        return redirect("forums:thread_detail", slug=thread.slug)
    
    context = {
        "reply": reply,
        "thread": thread,
    }
    
    return render(request, "forums/reply_confirm_delete.html", context)


@login_required
@require_http_methods(["POST"])
def vote(request):
    """Handle voting on threads and replies."""
    content_type_id = request.POST.get("content_type")
    object_id = request.POST.get("object_id")
    vote_type = request.POST.get("vote_type")
    
    if not all([content_type_id, object_id, vote_type]):
        return JsonResponse({"error": _("Missing parameters")}, status=400)
    
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
    except (ContentType.DoesNotExist, Exception):
        return JsonResponse({"error": _("Content not found")}, status=404)
    
    # Check if user already voted
    vote_obj, created = Vote.objects.get_or_create(
        content_type=content_type,
        object_id=object_id,
        user=request.user,
        defaults={"vote_type": vote_type}
    )
    
    if not created:
        # Toggle vote if same type, update if different
        if vote_obj.vote_type == vote_type:
            vote_obj.delete()
            count = Vote.objects.filter(
                content_type=content_type,
                object_id=object_id,
                vote_type=Vote.VoteType.UPVOTE
            ).count() - Vote.objects.filter(
                content_type=content_type,
                object_id=object_id,
                vote_type=Vote.VoteType.DOWNVOTE
            ).count()
            return JsonResponse({"success": True, "vote_type": None, "count": count})
        else:
            vote_obj.vote_type = vote_type
            vote_obj.save()
    
    count = Vote.objects.filter(
        content_type=content_type,
        object_id=object_id,
        vote_type=Vote.VoteType.UPVOTE
    ).count() - Vote.objects.filter(
        content_type=content_type,
        object_id=object_id,
        vote_type=Vote.VoteType.DOWNVOTE
    ).count()
    
    current_vote = Vote.objects.filter(
        content_type=content_type,
        object_id=object_id,
        user=request.user
    ).first()
    
    return JsonResponse({
        "success": True,
        "vote_type": current_vote.vote_type if current_vote else None,
        "count": count
    })


@login_required
def flag_content(request):
    """Flag/report content."""
    content_type_id = None
    object_id = None
    
    if request.method == "POST":
        content_type_id = request.POST.get("content_type")
        object_id = request.POST.get("object_id")
    else:
        content_type_id = request.GET.get("content_type")
        object_id = request.GET.get("object_id")
    
    if request.method == "POST":
        if not all([content_type_id, object_id]):
            messages.error(request, _("Missing parameters"))
            return redirect("forums:category_list")
        
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
            obj = content_type.get_object_for_this_type(pk=object_id)
        except (ContentType.DoesNotExist, Exception):
            messages.error(request, _("Content not found"))
            return redirect("forums:category_list")
        
        form = FlagForm(request.POST)
        if form.is_valid():
            flag = form.save(commit=False)
            flag.reporter = request.user
            flag.content_type = content_type
            flag.object_id = object_id
            flag.save()
            
            messages.success(request, _("Content flagged. Thank you for your report."))
            
            if request.htmx:
                return render(request, "forums/partials/flag_success.html")
            
            if hasattr(obj, 'get_absolute_url'):
                return redirect(obj.get_absolute_url())
            return redirect("forums:category_list")
    else:
        form = FlagForm()
    
    context = {
        "form": form,
        "content_type_id": content_type_id,
        "object_id": object_id,
    }
    
    return render(request, "forums/flag_form.html", context)


@login_required
def notification_list(request):
    """List user's notifications."""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
    }
    
    return render(request, "forums/notifications/list.html", context)


@login_required
@require_http_methods(["POST"])
def notification_mark_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.htmx:
        return render(request, "forums/partials/notification_item.html", {"notification": notification})
    
    return redirect("forums:notification_list")


@login_required
@moderator_required
def moderation_dashboard(request):
    """Moderation dashboard."""
    # Pending content
    pending_threads = Thread.objects.filter(is_approved=False)
    pending_replies = Reply.objects.filter(is_approved=False)
    
    # Flagged content
    flagged_content = Flag.objects.filter(status=Flag.Status.PENDING)
    
    # Recent moderator actions
    recent_actions = ModeratorAction.objects.all()[:50]
    
    context = {
        "pending_threads": pending_threads,
        "pending_replies": pending_replies,
        "flagged_content": flagged_content,
        "recent_actions": recent_actions,
    }
    
    return render(request, "forums/moderation/dashboard.html", context)


@login_required
@moderator_required
@require_http_methods(["POST"])
def thread_lock(request, slug):
    """Lock/unlock a thread."""
    thread = get_object_or_404(Thread, slug=slug)
    thread.is_locked = not thread.is_locked
    thread.save()
    
    # Log action
    ModeratorAction.objects.create(
        moderator=request.user,
        action_type=ModeratorAction.ActionType.LOCK if thread.is_locked else ModeratorAction.ActionType.UNLOCK,
        content_type=ContentType.objects.get_for_model(Thread),
        object_id=thread.pk,
    )
    
    messages.success(request, _("Thread locked.") if thread.is_locked else _("Thread unlocked."))
    return redirect("forums:thread_detail", slug=thread.slug)


@login_required
@moderator_required
@require_http_methods(["POST"])
def thread_pin(request, slug):
    """Pin/unpin a thread."""
    thread = get_object_or_404(Thread, slug=slug)
    thread.is_pinned = not thread.is_pinned
    thread.save()
    
    # Log action
    ModeratorAction.objects.create(
        moderator=request.user,
        action_type=ModeratorAction.ActionType.PIN if thread.is_pinned else ModeratorAction.ActionType.UNPIN,
        content_type=ContentType.objects.get_for_model(Thread),
        object_id=thread.pk,
    )
    
    messages.success(request, _("Thread pinned.") if thread.is_pinned else _("Thread unpinned."))
    return redirect("forums:category_detail", slug=thread.category.slug)


@login_required
@moderator_required
@require_http_methods(["POST"])
def approve_content(request):
    """Approve pending content."""
    content_type_id = request.POST.get("content_type")
    object_id = request.POST.get("object_id")
    
    if not all([content_type_id, object_id]):
        messages.error(request, _("Missing parameters"))
        return redirect("forums:moderation_dashboard")
    
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
    except (ContentType.DoesNotExist, obj.DoesNotExist):
        messages.error(request, _("Content not found"))
        return redirect("forums:moderation_dashboard")
    
    obj.is_approved = True
    obj.save()
    
    # Create notification
    if obj.author and hasattr(obj, 'thread'):
        Notification.objects.create(
            recipient=obj.author,
            notification_type=Notification.NotificationType.CONTENT_APPROVED,
            content_type=content_type,
            object_id=object_id,
            message=_("Your %(type)s has been approved.") % {"type": "reply" if isinstance(obj, Reply) else "thread"}
        )
    
    # Log action
    ModeratorAction.objects.create(
        moderator=request.user,
        action_type=ModeratorAction.ActionType.APPROVE,
        content_type=content_type,
        object_id=object_id,
    )
    
    messages.success(request, _("Content approved."))
    return redirect("forums:moderation_dashboard")


@login_required
@moderator_required
@require_http_methods(["POST"])
def reject_content(request):
    """Reject pending content."""
    content_type_id = request.POST.get("content_type")
    object_id = request.POST.get("object_id")
    reason = request.POST.get("reason", "")
    
    if not all([content_type_id, object_id]):
        messages.error(request, _("Missing parameters"))
        return redirect("forums:moderation_dashboard")
    
    try:
        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
    except (ContentType.DoesNotExist, obj.DoesNotExist):
        messages.error(request, _("Content not found"))
        return redirect("forums:moderation_dashboard")
    
    # Create notification
    if obj.author:
        Notification.objects.create(
            recipient=obj.author,
            notification_type=Notification.NotificationType.CONTENT_REJECTED,
            content_type=content_type,
            object_id=object_id,
            message=_("Your %(type)s has been rejected. %(reason)s") % {
                "type": "reply" if isinstance(obj, Reply) else "thread",
                "reason": reason if reason else ""
            }
        )
    
    # Log action before deleting
    ModeratorAction.objects.create(
        moderator=request.user,
        action_type=ModeratorAction.ActionType.REJECT,
        content_type=content_type,
        object_id=object_id,
        reason=reason,
    )
    
    # Delete rejected content
    obj.delete()
    
    messages.success(request, _("Content rejected and deleted."))
    return redirect("forums:moderation_dashboard")

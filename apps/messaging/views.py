from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Count
from django.utils.translation import gettext_lazy as _
from django.contrib import messages as django_messages
from django.utils import timezone
from django.urls import reverse
from .models import Conversation, Message, UserPresence
from .forms import AdminMessageForm

User = get_user_model()


def admin_or_board_check(user):
    """Check if user is admin or board member."""
    return user.is_authenticated and (user.is_admin() or user.is_board_member())


@login_required
def chat_list(request):
    """List all conversations for the current user."""
    from django.core.paginator import Paginator
    
    conversations = Conversation.objects.filter(
        participants=request.user
    ).select_related().prefetch_related('participants', 'messages').annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(conversations, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Add other participant to each conversation
    for conversation in page_obj:
        conversation.other_participant = conversation.get_other_participant(request.user)
    
    # Get online users
    online_users = UserPresence.get_online_users().select_related('user').exclude(user=request.user)
    
    # Check if a conversation should be auto-loaded (from URL parameter or direct access)
    conversation_id = request.GET.get('conversation', None)
    initial_conversation = None
    if conversation_id:
        try:
            initial_conversation = Conversation.objects.filter(
                participants=request.user,
                id=conversation_id
            ).first()
        except (ValueError, TypeError):
            pass
    
    context = {
        'page_obj': page_obj,
        'online_users': [presence.user for presence in online_users],
        'initial_conversation_id': conversation_id if initial_conversation else None,
    }
    
    # Check if this is an HTMX request for partial update
    if request.headers.get('HX-Request'):
        return render(request, 'messaging/partials/conversations_list.html', context)
    
    return render(request, 'messaging/chat_list.html', context)


@login_required
def chat_detail(request, conversation_id):
    """Chat detail view for a specific conversation."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Get last message ID from GET parameter for HTMX polling (to check for new messages)
    requested_last_id = request.GET.get('last_message_id', None)
    
    # Mark messages as read
    conversation.mark_as_read(request.user)
    
    # Get messages - limit to latest 50 for initial load (older messages loaded via infinite scroll)
    all_messages = conversation.messages.all().order_by('created_at')
    message_count = all_messages.count()
    if message_count > 50:
        # Get the last 50 messages (most recent) - keep as queryset for template
        messages = all_messages[message_count - 50:]
    else:
        messages = all_messages
    other_user = conversation.get_other_participant(request.user)
    
    # If HTMX request and we have last_message_id parameter, only return new messages
    if request.headers.get('HX-Request') and requested_last_id:
        try:
            last_id = int(requested_last_id)
            # Only query if last_id > 0 (0 means no messages yet or initial load)
            if last_id > 0:
                # Query the database for new messages (not the list)
                new_messages_queryset = conversation.messages.filter(id__gt=last_id).order_by('created_at')
                if new_messages_queryset.exists():
                    context = {
                        'messages': new_messages_queryset,
                        'conversation': conversation,
                        'other_user': other_user,
                        'user': request.user,
                    }
                    return render(request, 'messaging/partials/messages_list.html', context)
            
            # No new messages, return empty response
            return HttpResponse(status=204)  # No Content
        except (ValueError, TypeError) as e:
            # Log error but don't crash - return empty response
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing last_message_id: {e}")
            return HttpResponse(status=204)  # No Content
    
    # Get last message ID for polling (compute from messages)
    last_message_id = 0
    if messages:
        try:
            if hasattr(messages, 'last'):
                last_msg = messages.last()
                if last_msg:
                    last_message_id = last_msg.id
            elif hasattr(messages, '__len__') and len(messages) > 0:
                # It's a list or queryset slice
                last_message_id = messages[len(messages) - 1].id if hasattr(messages[len(messages) - 1], 'id') else 0
        except (AttributeError, IndexError, TypeError):
            last_message_id = 0
    
    context = {
        'conversation': conversation,
        'messages': messages,
        'other_user': other_user,
        'user': request.user,
        'last_message_id': last_message_id,
    }
    
    # Check if this is an HTMX request for partial update (full conversation load)
    if request.headers.get('HX-Request') and not requested_last_id:
        # Return partial conversation view for HTMX (when clicking on conversation)
        return render(request, 'messaging/partials/chat_detail.html', context)
    
    # For direct page access (not HTMX), redirect to chat_list with conversation parameter
    # This ensures consistent layout and prevents plain text display
    return redirect(f"{reverse('messaging:chat_list')}?conversation={conversation_id}")


@login_required
def start_conversation(request, user_id):
    """Start a conversation with another user."""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Cannot start conversation with yourself'}, status=400)
        # Redirect to chat list with error message
        from django.contrib import messages
        messages.error(request, _('Cannot start conversation with yourself.'))
        return redirect('messaging:chat_list')
    
    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    # If HTMX request, return the conversation view
    if request.headers.get('HX-Request'):
        messages_queryset = conversation.messages.all().order_by('created_at')
        message_count = messages_queryset.count()
        if message_count > 50:
            messages = messages_queryset[message_count - 50:]
        else:
            messages = messages_queryset
        
        # Get last message ID
        last_msg_id = 0
        if messages:
            try:
                if hasattr(messages, 'last'):
                    last_msg = messages.last()
                    if last_msg:
                        last_msg_id = last_msg.id
                elif hasattr(messages, '__len__') and len(messages) > 0:
                    last_msg_id = messages[len(messages) - 1].id if hasattr(messages[len(messages) - 1], 'id') else 0
            except (AttributeError, IndexError, TypeError):
                last_msg_id = 0
        
        conversation.mark_as_read(request.user)
        context = {
            'conversation': conversation,
            'messages': messages,
            'other_user': other_user,
            'user': request.user,
            'last_message_id': last_msg_id,
        }
        return render(request, 'messaging/partials/chat_detail.html', context)
    
    return redirect('messaging:chat_detail', conversation_id=conversation.id)


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message via AJAX or HTMX."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content', '').strip()
    if not content:
        if request.headers.get('HX-Request'):
            return HttpResponse('Message content is required', status=400)
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    # Check for duplicate message (same content within last 3 seconds)
    from django.utils import timezone
    from datetime import timedelta
    recent_duplicate = Message.objects.filter(
        conversation=conversation,
        sender=request.user,
        content=content,
        created_at__gte=timezone.now() - timedelta(seconds=3)
    ).first()
    
    if recent_duplicate:
        # Return the existing message instead of creating duplicate
        if request.headers.get('HX-Request'):
            context = {
                'messages': [recent_duplicate],
                'conversation': conversation,
                'other_user': conversation.get_other_participant(request.user),
                'user': request.user,
            }
            return render(request, 'messaging/partials/messages_list.html', context)
        return JsonResponse({
            'success': True,
            'message': {
                'id': recent_duplicate.id,
                'content': recent_duplicate.content,
                'sender': request.user.full_name,
                'created_at': recent_duplicate.created_at.isoformat(),
            }
        })
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
    # If HTMX request, return only the new message as HTML
    if request.headers.get('HX-Request'):
        # Return only the new message
        context = {
            'messages': [message],  # Only the new message
            'conversation': conversation,
            'other_user': conversation.get_other_participant(request.user),
            'user': request.user,
        }
        response = render(request, 'messaging/partials/messages_list.html', context)
        # Trigger scroll and clear input
        response['HX-Trigger'] = 'newMessage'
        return response
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender': request.user.full_name,
            'created_at': message.created_at.isoformat(),
        }
    })


@login_required
def online_users(request):
    """Get list of online users."""
    online_presences = UserPresence.get_online_users().exclude(user=request.user)
    online_users_list = [presence.user for presence in online_presences]
    
    # If HTMX request, return partial HTML
    if request.headers.get('HX-Request'):
        context = {'online_users': online_users_list}
        return render(request, 'messaging/partials/online_users.html', context)
    
    users = [{'id': p.user.id, 'name': p.user.full_name} for p in online_presences]
    return JsonResponse({'users': users})


@login_required
def check_user_status(request, user_id):
    """Check if a specific user is online."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        presence = UserPresence.objects.filter(user=user).first()
        
        is_online = presence.is_online if presence else False
        last_seen = presence.last_seen if presence else None
        
        return JsonResponse({
            'is_online': is_online,
            'last_seen': last_seen.isoformat() if last_seen else None,
            'user_id': user_id
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, conversation_id):
    """Mark all messages in a conversation as read."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    conversation.mark_as_read(request.user)
    return JsonResponse({'success': True})


@login_required
def get_messages(request, conversation_id):
    """Get messages for a conversation with pagination."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    offset = (page - 1) * per_page
    
    # Get messages
    messages = conversation.messages.all().order_by('-created_at')[offset:offset + per_page]
    
    # Mark as read when fetching
    conversation.mark_as_read(request.user)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.full_name,
        'sender_id': msg.sender.id,
        'created_at': msg.created_at.isoformat(),
        'is_read': msg.is_read,
    } for msg in reversed(messages)]  # Reverse to get chronological order
    
    return JsonResponse({
        'messages': messages_data,
        'has_more': conversation.messages.count() > offset + per_page
    })


@login_required
def unread_count(request):
    """Get total unread message count for the current user."""
    unread_count = Message.objects.filter(
        conversation__participants=request.user
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).count()
    
    # Count admin messages separately for emphasis
    admin_unread_count = Message.objects.filter(
        conversation__participants=request.user,
        is_admin_message=True
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).count()
    
    return JsonResponse({
        'unread_count': unread_count,
        'admin_unread_count': admin_unread_count
    })


@login_required
@user_passes_test(admin_or_board_check)
def admin_messaging(request):
    """Admin interface for sending messages to users."""
    if request.method == 'POST':
        form = AdminMessageForm(request.POST)
        if form.is_valid():
            recipient_type = form.cleaned_data['recipient_type']
            content = form.cleaned_data['content']
            subject = form.cleaned_data.get('subject', '')
            
            # Determine recipients based on type
            if recipient_type == 'all':
                recipients = User.objects.filter(is_active=True).exclude(id=request.user.id)
            elif recipient_type == 'all_members':
                recipients = User.objects.filter(
                    is_active=True,
                    role__in=['member', 'board']
                ).exclude(id=request.user.id)
            elif recipient_type == 'active_members':
                from apps.members.models import Member
                active_member_ids = Member.objects.filter(
                    status=Member.MembershipStatus.ACTIVE
                ).values_list('user_id', flat=True)
                recipients = User.objects.filter(
                    id__in=active_member_ids,
                    is_active=True
                ).exclude(id=request.user.id)
            else:  # selected
                recipients = form.cleaned_data['selected_users'].exclude(id=request.user.id)
            
            # Send message to each recipient
            sent_count = 0
            failed_count = 0
            failed_details = []
            
            for recipient in recipients:
                try:
                    # Check if conversation exists (same logic as start_conversation)
                    conversation = Conversation.objects.filter(
                        participants=request.user
                    ).filter(
                        participants=recipient
                    ).first()
                    
                    if not conversation:
                        # Create new conversation
                        conversation = Conversation.objects.create()
                        conversation.participants.add(request.user, recipient)
                    
                    # Create message with subject if provided
                    message_content = content
                    if subject:
                        message_content = f"**{subject}**\n\n{content}"
                    
                    # Create message - use create() which will trigger save() and set is_admin_message
                    message = Message.objects.create(
                        conversation=conversation,
                        sender=request.user,
                        content=message_content
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    error_msg = f"{recipient.email}: {str(e)}"
                    failed_details.append(error_msg)
                    print(f"Failed to send message to {recipient.email}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Show success message
            if sent_count > 0:
                django_messages.success(
                    request,
                    _('Successfully sent message to {count} user(s).').format(count=sent_count)
                )
            if failed_count > 0:
                error_detail = ' '.join(failed_details[:3])  # Show first 3 errors
                if len(failed_details) > 3:
                    error_detail += f' ... and {len(failed_details) - 3} more'
                django_messages.error(
                    request,
                    _('Failed to send message to {count} user(s). Details: {details}').format(
                        count=failed_count,
                        details=error_detail
                    )
                )
            
            return redirect('messaging:admin_messaging')
    else:
        form = AdminMessageForm()
    
    # Get statistics for the admin messaging page
    total_users = User.objects.filter(is_active=True).exclude(id=request.user.id).count()
    from apps.members.models import Member
    active_members_count = Member.objects.filter(
        status=Member.MembershipStatus.ACTIVE
    ).count()
    all_members_count = Member.objects.count()
    
    # Get recent admin messages sent
    recent_admin_messages = Message.objects.filter(
        sender=request.user,
        is_admin_message=True
    ).order_by('-created_at')[:10]
    
    context = {
        'form': form,
        'total_users': total_users,
        'active_members_count': active_members_count,
        'all_members_count': all_members_count,
        'recent_admin_messages': recent_admin_messages,
    }
    
    return render(request, 'messaging/admin_messaging.html', context)


@login_required
@user_passes_test(admin_or_board_check)
def get_users_list(request):
    """API endpoint to get list of users for admin messaging."""
    search = request.GET.get('search', '')
    users = User.objects.filter(is_active=True).exclude(
        id=request.user.id
    ).exclude(
        role__in=['admin']
    )
    
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    users_data = [{
        'id': user.id,
        'name': user.full_name,
        'email': user.email,
        'role': user.get_role_display() if hasattr(user, 'get_role_display') else user.role,
    } for user in users[:100]]  # Limit to 100 for performance
    
    return JsonResponse({'users': users_data})


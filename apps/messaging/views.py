from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Count
from django.utils.translation import gettext_lazy as _
from .models import Conversation, Message, UserPresence

User = get_user_model()


@login_required
def chat_list(request):
    """List all conversations for the current user."""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-updated_at')
    
    # Add other participant to each conversation
    for conversation in conversations:
        conversation.other_participant = conversation.get_other_participant(request.user)
    
    # Get online users
    online_users = UserPresence.get_online_users().exclude(user=request.user)
    
    context = {
        'conversations': conversations,
        'online_users': [presence.user for presence in online_users],
    }
    return render(request, 'messaging/chat_list.html', context)


@login_required
def chat_detail(request, conversation_id):
    """Chat detail view for a specific conversation."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Mark messages as read
    conversation.mark_as_read(request.user)
    
    # Get messages
    messages = conversation.messages.all().order_by('created_at')
    other_user = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'messages': messages,
        'other_user': other_user,
    }
    return render(request, 'messaging/chat_detail.html', context)


@login_required
@require_http_methods(["POST"])
def start_conversation(request, user_id):
    """Start a conversation with another user."""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        return JsonResponse({'error': 'Cannot start conversation with yourself'}, status=400)
    
    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return redirect('messaging:chat_detail', conversation_id=conversation.id)


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message via AJAX."""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
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
    users = [{'id': p.user.id, 'name': p.user.full_name} for p in online_presences]
    return JsonResponse({'users': users})


"""Utility functions for real-time forum updates."""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_thread_update(thread, update_type='new'):
    """Broadcast thread update to all subscribed users."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f"forum_category_{thread.category.id}",
        {
            "type": "thread_update",
            "thread": {
                "id": thread.id,
                "title": thread.title,
                "slug": thread.slug,
                "author": thread.author.full_name,
                "update_type": update_type,
            }
        }
    )


def broadcast_reply_update(reply, thread):
    """Broadcast new reply to thread subscribers."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Notify thread author
    if reply.author.id != thread.author.id:
        async_to_sync(channel_layer.group_send)(
            f"user_{thread.author.id}_notifications",
            {
                "type": "notification_message",
                "notification": {
                    "type": "new_reply",
                    "title": f"New reply to '{thread.title[:50]}'",
                    "message": f"{reply.author.full_name} replied to your thread",
                    "url": f"/forums/thread/{thread.slug}/",
                }
            }
        )
    
    # Broadcast to thread viewers
    async_to_sync(channel_layer.group_send)(
        f"thread_{thread.id}",
        {
            "type": "reply_update",
            "reply": {
                "id": reply.id,
                "author": reply.author.full_name,
                "author_id": reply.author.id,
                "content": reply.content[:200],  # Preview
                "created_at": reply.created_at.isoformat(),
            }
        }
    )


def broadcast_thread_activity(thread_id, activity_type, data):
    """Broadcast general thread activity."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    async_to_sync(channel_layer.group_send)(
        f"thread_{thread_id}",
        {
            "type": "activity_update",
            "activity_type": activity_type,
            "data": data,
        }
    )







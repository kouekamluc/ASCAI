from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message

try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
except ImportError:
    channel_layer = None


@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    """Send WebSocket notification when a new message is created."""
    if created and channel_layer:
        conversation = instance.conversation
        # Get the other participant(s)
        other_participants = conversation.participants.exclude(id=instance.sender.id)
        
        for participant in other_participants:
            # Send notification to participant's personal channel
            async_to_sync(channel_layer.group_send)(
                f"user_{participant.id}",
                {
                    "type": "new_message",
                    "message": {
                        "id": instance.id,
                        "conversation_id": conversation.id,
                        "sender": instance.sender.full_name,
                        "sender_id": instance.sender.id,
                        "content": instance.content[:100],  # Preview
                        "created_at": instance.created_at.isoformat(),
                    }
                }
            )
        
        # Also notify in conversation channel
        async_to_sync(channel_layer.group_send)(
            f"conversation_{conversation.id}",
            {
                "type": "message_update",
                "message": {
                    "id": instance.id,
                    "sender": instance.sender.full_name,
                    "sender_id": instance.sender.id,
                    "content": instance.content,
                    "created_at": instance.created_at.isoformat(),
                    "is_read": instance.is_read,
                }
            }
        )


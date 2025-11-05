from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
import logging

logger = logging.getLogger(__name__)

try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
except ImportError:
    channel_layer = None


def send_email_notification(recipient, sender, message_content, conversation_id):
    """
    Send email notification for admin messages.
    For now, this logs to console (local development).
    In production, this would send actual emails.
    """
    # Local email notification (console logging)
    logger.info("=" * 80)
    logger.info("EMAIL NOTIFICATION (Local Development Mode)")
    logger.info("=" * 80)
    logger.info(f"To: {recipient.email}")
    logger.info(f"From: ASCAI Admin <admin@ascai.org>")
    logger.info(f"Subject: New Message from {sender.full_name} - ASCAI")
    logger.info("-" * 80)
    logger.info(f"Dear {recipient.full_name},")
    logger.info("")
    logger.info(f"You have received a new message from {sender.full_name} ({sender.email}).")
    logger.info("")
    logger.info("Message:")
    logger.info("-" * 80)
    logger.info(message_content)
    logger.info("-" * 80)
    logger.info("")
    logger.info(f"Please log in to your ASCAI account to view and respond to this message.")
    logger.info("")
    logger.info("Best regards,")
    logger.info("ASCAI Team")
    logger.info("=" * 80)
    print()  # Add extra line for readability


@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    """Send WebSocket notification when a new message is created."""
    if not created:
        return
    
    conversation = instance.conversation
    # Get the other participant(s)
    other_participants = conversation.participants.exclude(id=instance.sender.id)
    
    # Send email notification if message is from admin/board member
    if instance.is_admin_message:
        for participant in other_participants:
            send_email_notification(
                recipient=participant,
                sender=instance.sender,
                message_content=instance.content,
                conversation_id=conversation.id
            )
    
    # Send WebSocket notifications
    if channel_layer:
        try:
            for participant in other_participants:
                # Send notification to participant's personal channel
                try:
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
                                "is_admin_message": instance.is_admin_message,
                            }
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification to user {participant.id}: {e}")
            
            # Also notify in conversation channel
            try:
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
                            "is_admin_message": instance.is_admin_message,
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send message update to conversation {conversation.id}: {e}")
        except Exception as e:
            logger.error(f"Error sending WebSocket notifications: {e}")
            # Don't fail the signal if WebSocket fails


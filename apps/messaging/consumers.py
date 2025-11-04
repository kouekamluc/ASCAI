import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, UserPresence

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat."""
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # User's personal channel for notifications
        self.user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        
        # Mark user as online
        await self.update_presence(True)
        
        await self.accept()
        
        # Notify others that user is online
        await self.broadcast_presence_update()
    
    async def disconnect(self, close_code):
        # Mark user as offline
        await self.update_presence(False)
        
        # Notify others that user is offline
        await self.broadcast_presence_update()
        
        # Leave all groups
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        
        # Leave conversation groups
        conversations = await self.get_user_conversations()
        for conv_id in conversations:
            await self.channel_layer.group_discard(
                f"conversation_{conv_id}",
                self.channel_name
            )
    
    @database_sync_to_async
    def update_presence(self, is_online):
        """Update user's online presence."""
        UserPresence.update_presence(self.user, is_online)
    
    @database_sync_to_async
    def get_user_conversations(self):
        """Get all conversation IDs for the user."""
        return list(
            Conversation.objects.filter(participants=self.user)
            .values_list('id', flat=True)
        )
    
    async def broadcast_presence_update(self):
        """Broadcast presence update to user's contacts."""
        conversations = await self.get_user_conversations()
        for conv_id in conversations:
            await self.channel_layer.group_send(
                f"conversation_{conv_id}",
                {
                    "type": "presence_update",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "is_online": await database_sync_to_async(
                        lambda: UserPresence.objects.get(user=self.user).is_online
                    )(),
                }
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'join_conversation':
            conversation_id = data.get('conversation_id')
            await self.channel_layer.group_add(
                f"conversation_{conversation_id}",
                self.channel_name
            )
            await self.send(text_data=json.dumps({
                'type': 'joined_conversation',
                'conversation_id': conversation_id
            }))
        
        elif message_type == 'leave_conversation':
            conversation_id = data.get('conversation_id')
            await self.channel_layer.group_discard(
                f"conversation_{conversation_id}",
                self.channel_name
            )
        
        elif message_type == 'send_message':
            conversation_id = data.get('conversation_id')
            content = data.get('content')
            
            # Save message to database
            message = await self.save_message(conversation_id, content)
            
            # Broadcast to conversation group
            await self.channel_layer.group_send(
                f"conversation_{conversation_id}",
                {
                    "type": "message_update",
                    "message": {
                        "id": message['id'],
                        "sender": self.user.full_name,
                        "sender_id": self.user.id,
                        "content": message['content'],
                        "created_at": message['created_at'],
                        "is_read": False,
                    }
                }
            )
        
        elif message_type == 'typing':
            conversation_id = data.get('conversation_id')
            is_typing = data.get('is_typing', True)
            
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                f"conversation_{conversation_id}",
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "user_name": self.user.full_name,
                    "is_typing": is_typing,
                }
            )
    
    @database_sync_to_async
    def save_message(self, conversation_id, content):
        """Save message to database."""
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        return {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
        }
    
    # Handler methods for group messages
    async def message_update(self, event):
        """Send message update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))
    
    async def new_message(self, event):
        """Send new message notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['message']
        }))
    
    async def presence_update(self, event):
        """Send presence update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_online': event['is_online'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        if event['user_id'] != self.user.id:  # Don't send own typing indicator
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications (forum, etc.)."""
    
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # User's notification channel
        self.user_group = f"user_{self.user.id}_notifications"
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        pass  # Notifications are pushed from server
    
    async def notification_message(self, event):
        """Send notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }))







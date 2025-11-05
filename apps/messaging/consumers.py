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
        try:
            self.user = self.scope.get("user")
            if not self.user or not self.user.is_authenticated:
                await self.close(code=4001)  # Unauthorized
                return
            
            # User's personal channel for notifications
            self.user_group = f"user_{self.user.id}"
            if self.channel_layer:
                await self.channel_layer.group_add(self.user_group, self.channel_name)
            
            # Mark user as online
            await self.update_presence(True)
            
            await self.accept()
            
            # Notify others that user is online
            await self.broadcast_presence_update()
        except Exception as e:
            print(f"Error in WebSocket connect: {e}")
            import traceback
            traceback.print_exc()
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'user') and self.user and self.user.is_authenticated:
                # Mark user as offline
                await self.update_presence(False)
                
                # Notify others that user is offline
                await self.broadcast_presence_update()
                
                # Leave all groups
                if hasattr(self, 'user_group') and self.channel_layer:
                    await self.channel_layer.group_discard(self.user_group, self.channel_name)
                
                # Leave conversation groups
                if self.channel_layer:
                    conversations = await self.get_user_conversations()
                    for conv_id in conversations:
                        await self.channel_layer.group_discard(
                            f"conversation_{conv_id}",
                            self.channel_name
                        )
        except Exception as e:
            print(f"Error in WebSocket disconnect: {e}")
            import traceback
            traceback.print_exc()
    
    @database_sync_to_async
    def update_presence(self, is_online):
        """Update user's online presence."""
        try:
            UserPresence.update_presence(self.user, is_online)
        except Exception as e:
            # Log error but don't fail connection
            print(f"Error updating presence: {e}")
    
    @database_sync_to_async
    def get_user_conversations(self):
        """Get all conversation IDs for the user."""
        return list(
            Conversation.objects.filter(participants=self.user)
            .values_list('id', flat=True)
        )
    
    async def broadcast_presence_update(self):
        """Broadcast presence update to user's contacts."""
        try:
            if not self.channel_layer or not hasattr(self, 'user') or not self.user:
                return
                
            conversations = await self.get_user_conversations()
            is_online = await database_sync_to_async(
                lambda: UserPresence.objects.filter(user=self.user).first()
            )()
            online_status = is_online.is_online if is_online else False
            
            for conv_id in conversations:
                await self.channel_layer.group_send(
                    f"conversation_{conv_id}",
                    {
                        "type": "presence_update",
                        "user_id": self.user.id,
                        "user_name": self.user.full_name,
                        "is_online": online_status,
                    }
                )
        except Exception as e:
            print(f"Error broadcasting presence: {e}")
            import traceback
            traceback.print_exc()
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'leave_conversation':
            conversation_id = data.get('conversation_id')
            await self.channel_layer.group_discard(
                f"conversation_{conversation_id}",
                self.channel_name
            )
        
        elif message_type == 'send_message':
            conversation_id = data.get('conversation_id')
            content = data.get('content')
            
            try:
                # Save message to database
                message = await self.save_message(conversation_id, content)
                
                # Broadcast to conversation group
                if self.channel_layer:
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
            except ValueError as e:
                # Send error back to client
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
            except Exception as e:
                # Send generic error for unexpected exceptions
                print(f"Error sending message: {e}")
                import traceback
                traceback.print_exc()
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to send message. Please try again.'
                }))
        
        elif message_type == 'typing':
            conversation_id = data.get('conversation_id')
            is_typing = data.get('is_typing', True)
            
            # Verify user has access to conversation
            conversations = await self.get_user_conversations()
            if conversation_id not in conversations:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Access denied to conversation'
                }))
                return
            
            # Broadcast typing indicator
            if self.channel_layer:
                await self.channel_layer.group_send(
                    f"conversation_{conversation_id}",
                    {
                        "type": "typing_indicator",
                        "user_id": self.user.id,
                        "user_name": self.user.full_name,
                        "is_typing": is_typing,
                    }
                )
        
        elif message_type == 'mark_read':
            conversation_id = data.get('conversation_id')
            await self.mark_conversation_as_read(conversation_id)
        
        elif message_type == 'join_conversation':
            conversation_id = data.get('conversation_id')
            # Verify access before joining
            conversations = await self.get_user_conversations()
            if conversation_id not in conversations:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Access denied to conversation'
                }))
                return
            if self.channel_layer:
                await self.channel_layer.group_add(
                    f"conversation_{conversation_id}",
                    self.channel_name
                )
            # Mark messages as read when joining
            await self.mark_conversation_as_read(conversation_id)
            await self.send(text_data=json.dumps({
                'type': 'joined_conversation',
                'conversation_id': conversation_id
            }))
    
    @database_sync_to_async
    def save_message(self, conversation_id, content):
        """Save message to database."""
        try:
            if not hasattr(self, 'user') or not self.user:
                raise ValueError("User not authenticated")
                
            conversation = Conversation.objects.filter(
                participants=self.user
            ).get(id=conversation_id)
        except Conversation.DoesNotExist:
            raise ValueError("Conversation not found or access denied")
        except Exception as e:
            raise ValueError(f"Error accessing conversation: {str(e)}")
        
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")
        
        try:
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content.strip()
            )
            return {
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
            }
        except Exception as e:
            raise ValueError(f"Failed to save message: {str(e)}")
    
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
    
    @database_sync_to_async
    def mark_conversation_as_read(self, conversation_id):
        """Mark all messages in conversation as read for current user."""
        try:
            if not hasattr(self, 'user') or not self.user:
                return
            conversation = Conversation.objects.filter(
                participants=self.user
            ).get(id=conversation_id)
            conversation.mark_as_read(self.user)
        except (Conversation.DoesNotExist, Exception):
            pass  # Silently fail if conversation doesn't exist or user doesn't have access


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications (forum, etc.)."""
    
    async def connect(self):
        try:
            self.user = self.scope.get("user")
            if not self.user or not self.user.is_authenticated:
                await self.close(code=4001)
                return
            
            # User's notification channel
            self.user_group = f"user_{self.user.id}_notifications"
            if self.channel_layer:
                await self.channel_layer.group_add(self.user_group, self.channel_name)
            
            await self.accept()
        except Exception as e:
            print(f"Error in NotificationConsumer connect: {e}")
            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'user_group') and self.channel_layer:
                await self.channel_layer.group_discard(self.user_group, self.channel_name)
        except Exception as e:
            print(f"Error in NotificationConsumer disconnect: {e}")
    
    async def receive(self, text_data):
        """Receive message from WebSocket."""
        pass  # Notifications are pushed from server
    
    async def notification_message(self, event):
        """Send notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['notification']
        }))












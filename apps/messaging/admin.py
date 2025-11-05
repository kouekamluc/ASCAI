from django.contrib import admin
from .models import Conversation, Message, UserPresence


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__email', 'participants__first_name', 'participants__last_name')
    filter_horizontal = ('participants',)

    def get_participants(self, obj):
        return ", ".join([p.full_name for p in obj.participants.all()])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content_preview', 'is_read', 'is_admin_message', 'created_at')
    list_filter = ('is_read', 'is_admin_message', 'created_at', 'conversation')
    search_fields = ('content', 'sender__email', 'sender__first_name', 'sender__last_name')
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online', 'last_seen')
    list_filter = ('is_online', 'last_seen')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')












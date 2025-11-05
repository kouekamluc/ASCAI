from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('conversation/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversation/<int:conversation_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('conversation/<int:conversation_id>/messages/', views.get_messages, name='get_messages'),
    path('online-users/', views.online_users, name='online_users'),
    path('user/<int:user_id>/status/', views.check_user_status, name='check_user_status'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('admin/', views.admin_messaging, name='admin_messaging'),
    path('admin/users-list/', views.get_users_list, name='get_users_list'),
]












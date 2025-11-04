from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('conversation/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('online-users/', views.online_users, name='online_users'),
]







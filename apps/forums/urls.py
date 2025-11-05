"""
URL configuration for forums app.
"""

from django.urls import path
from . import views

app_name = "forums"

urlpatterns = [
    # Categories
    path("", views.category_list, name="category_list"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    
    # Threads
    path("thread/<slug:slug>/", views.thread_detail, name="thread_detail"),
    path("category/<slug:slug>/create/", views.thread_create, name="thread_create"),
    path("thread/<slug:slug>/edit/", views.thread_update, name="thread_update"),
    path("thread/<slug:slug>/delete/", views.thread_delete, name="thread_delete"),
    
    # Replies
    path("thread/<slug:slug>/reply/", views.reply_create, name="reply_create"),
    path("thread/<slug:slug>/reply/<int:reply_id>/edit/", views.reply_update, name="reply_update"),
    path("thread/<slug:slug>/reply/<int:reply_id>/delete/", views.reply_delete, name="reply_delete"),
    
    # Voting
    path("vote/", views.vote, name="vote"),
    
    # Flagging
    path("flag/", views.flag_content, name="flag_content"),
    
    # Notifications
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/<int:notification_id>/mark-read/", views.notification_mark_read, name="notification_mark_read"),
    
    # Moderation
    path("moderate/", views.moderation_dashboard, name="moderation_dashboard"),
    path("thread/<slug:slug>/lock/", views.thread_lock, name="thread_lock"),
    path("thread/<slug:slug>/pin/", views.thread_pin, name="thread_pin"),
    path("approve/", views.approve_content, name="approve_content"),
    path("reject/", views.reject_content, name="reject_content"),
]












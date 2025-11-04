"""
URL configuration for events app.
"""

from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("calendar/", views.event_calendar, name="calendar"),
    path("calendar/feed/", views.event_calendar_feed, name="calendar_feed"),
    path("create/", views.event_create, name="create"),
    path("<slug:slug>/", views.event_detail, name="detail"),
    path("<slug:slug>/edit/", views.event_edit, name="edit"),
    path("<slug:slug>/delete/", views.event_delete, name="delete"),
    path("<slug:slug>/register/", views.event_register, name="register"),
    path("<slug:slug>/unregister/", views.event_unregister, name="unregister"),
    path("<slug:slug>/attendees/", views.event_attendees, name="attendees"),
    path("<slug:slug>/check-in/<int:registration_id>/", views.event_check_in, name="check_in"),
    # Category management
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]


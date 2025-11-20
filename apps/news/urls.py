"""
URL configuration for news app.
"""

from django.urls import path
from . import views
from .feeds import LatestNewsFeed

app_name = "news"

urlpatterns = [
    # RSS Feed
    path("feed/", LatestNewsFeed(), name="feed"),
    path("", views.news_list, name="list"),
    path("create/", views.news_create, name="create"),
    path("<slug:slug>/", views.news_detail, name="detail"),
    path("<slug:slug>/edit/", views.news_edit, name="edit"),
    path("<slug:slug>/delete/", views.news_delete, name="delete"),
    # Category management
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]


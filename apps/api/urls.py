"""
URL configuration for API app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    NewsPostViewSet,
    NewsCategoryViewSet,
    EventViewSet,
    EventCategoryViewSet,
    MemberViewSet,
)

router = DefaultRouter()
router.register(r'news', NewsPostViewSet, basename='news')
router.register(r'news-categories', NewsCategoryViewSet, basename='news-category')
router.register(r'events', EventViewSet, basename='event')
router.register(r'event-categories', EventCategoryViewSet, basename='event-category')
router.register(r'members', MemberViewSet, basename='member')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
]


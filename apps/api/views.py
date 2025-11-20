"""
API views for ASCAI platform.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .serializers import (
    NewsPostSerializer,
    NewsCategorySerializer,
    EventSerializer,
    EventCategorySerializer,
    MemberPublicSerializer,
)
from apps.news.models import NewsPost, NewsCategory
from apps.events.models import Event, EventCategory
from apps.members.models import Member


class NewsPostViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news posts."""
    queryset = NewsPost.objects.filter(
        is_published=True,
        visibility=NewsPost.Visibility.PUBLIC
    ).select_related('author', 'category').order_by('-published_at', '-created_at')
    serializer_class = NewsPostSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    @method_decorator(ratelimit(key='ip', rate='100/h', method='GET'))
    def list(self, request, *args, **kwargs):
        """List news posts with pagination."""
        return super().list(request, *args, **kwargs)
    
    @method_decorator(ratelimit(key='ip', rate='100/h', method='GET'))
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single news post."""
        return super().retrieve(request, *args, **kwargs)


class NewsCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for news categories."""
    queryset = NewsCategory.objects.all()
    serializer_class = NewsCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for events."""
    queryset = Event.objects.filter(
        is_published=True,
        visibility=Event.Visibility.PUBLIC
    ).select_related('organizer', 'category').order_by('-start_date')
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    @method_decorator(ratelimit(key='ip', rate='100/h', method='GET'))
    def list(self, request, *args, **kwargs):
        """List events with pagination."""
        return super().list(request, *args, **kwargs)
    
    @method_decorator(ratelimit(key='ip', rate='100/h', method='GET'))
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single event."""
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def register(self, request, slug=None):
        """Register for an event."""
        event = self.get_object()
        # Registration logic would go here
        return Response({'message': 'Registration endpoint - to be implemented'})


class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for event categories."""
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class MemberViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for public member directory."""
    queryset = Member.objects.filter(
        status=Member.MembershipStatus.ACTIVE,
        profile_public=True
    ).select_related('user').order_by('-joined_date')
    serializer_class = MemberPublicSerializer
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='50/h', method='GET'))
    def list(self, request, *args, **kwargs):
        """List members with pagination."""
        return super().list(request, *args, **kwargs)


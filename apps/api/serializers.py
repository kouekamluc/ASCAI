"""
Serializers for ASCAI REST API.
"""
from rest_framework import serializers
from apps.news.models import NewsPost, NewsCategory
from apps.events.models import Event, EventCategory
from apps.members.models import Member
from apps.accounts.models import User


class NewsCategorySerializer(serializers.ModelSerializer):
    """Serializer for news categories."""
    
    class Meta:
        model = NewsCategory
        fields = ['id', 'name', 'slug', 'description']


class NewsPostSerializer(serializers.ModelSerializer):
    """Serializer for news posts."""
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = NewsPost
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content',
            'author_name', 'category_name', 'category_type',
            'visibility', 'featured_image', 'is_published',
            'published_at', 'created_at', 'views_count',
        ]
        read_only_fields = ['views_count', 'created_at', 'published_at']


class EventCategorySerializer(serializers.ModelSerializer):
    """Serializer for event categories."""
    
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'slug', 'description', 'color']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for events."""
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    registration_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'location',
            'start_date', 'end_date', 'organizer_name', 'category_name',
            'is_registration_required', 'max_attendees', 'registration_deadline',
            'visibility', 'is_published', 'featured_image',
            'created_at', 'views_count', 'registration_count',
        ]
        read_only_fields = ['views_count', 'created_at']
    
    def get_registration_count(self, obj):
        """Get number of registrations for this event."""
        return obj.registrations.filter(
            status__in=['registered', 'waitlisted']
        ).count()


class MemberPublicSerializer(serializers.ModelSerializer):
    """Public serializer for member directory (limited fields)."""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'user_name', 'user_email', 'membership_number',
            'status', 'category', 'university', 'course',
            'year_of_study', 'city', 'country_of_origin',
            'joined_date', 'is_verified',
        ]
        read_only_fields = ['joined_date']
    
    def get_user_email(self, obj):
        """Return email only if public."""
        if obj.email_public:
            return obj.user.email
        return None


"""
RSS feed for news posts.
"""
from django.contrib.syndication.views import Feed
from django.utils.translation import gettext_lazy as _
from .models import NewsPost


class LatestNewsFeed(Feed):
    """RSS feed for latest news posts."""
    
    title = _("ASCAI Latest News")
    link = "/news/"
    description = _("Latest news and announcements from ASCAI")
    
    def items(self):
        """Get latest 20 published news posts."""
        return NewsPost.objects.filter(
            is_published=True,
            visibility=NewsPost.Visibility.PUBLIC
        ).select_related('author', 'category').order_by('-published_at', '-created_at')[:20]
    
    def item_title(self, item):
        """Get item title."""
        return item.title
    
    def item_description(self, item):
        """Get item description."""
        return item.excerpt or item.content[:500]
    
    def item_pubdate(self, item):
        """Get item publication date."""
        return item.published_at or item.created_at
    
    def item_author_name(self, item):
        """Get item author name."""
        return item.author.full_name
    
    def item_categories(self, item):
        """Get item categories."""
        categories = []
        if item.category:
            categories.append(item.category.name)
        categories.append(item.get_category_type_display())
        return categories


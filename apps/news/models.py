"""
News and announcements models for ASCAI platform.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse


class NewsCategory(models.Model):
    """Category for news posts."""
    
    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("description"), blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("news category")
        verbose_name_plural = _("news categories")
        ordering = ["name"]
    
    def __str__(self):
        return self.name


class NewsPost(models.Model):
    """News post/announcement model."""
    
    class Category(models.TextChoices):
        IMPORTANT = "important", _("Important")
        GENERAL = "general", _("General")
        ACADEMIC = "academic", _("Academic")
        CULTURAL = "cultural", _("Cultural")
        SOCIAL = "social", _("Social")
    
    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        MEMBERS_ONLY = "members", _("Members Only")
        BOARD_ONLY = "board", _("Board Only")
    
    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    content = models.TextField(_("content"))
    excerpt = models.TextField(_("excerpt"), max_length=500, blank=True)
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_posts",
    )
    
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    
    category_type = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    
    featured_image = models.ImageField(
        _("featured image"),
        upload_to="news/",
        blank=True,
        null=True,
    )
    
    is_published = models.BooleanField(_("published"), default=False)
    published_at = models.DateTimeField(
        _("published at"),
        blank=True,
        null=True,
    )
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    views_count = models.PositiveIntegerField(_("views"), default=0)
    
    class Meta:
        verbose_name = _("news post")
        verbose_name_plural = _("news posts")
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["visibility"]),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("news:detail", kwargs={"slug": self.slug})
    
    def can_view(self, user):
        """Check if user can view this post."""
        if self.visibility == self.Visibility.PUBLIC:
            return True
        if not user.is_authenticated:
            return False
        if self.visibility == self.Visibility.MEMBERS_ONLY:
            return user.is_member()
        if self.visibility == self.Visibility.BOARD_ONLY:
            return user.is_board_member()
        return False

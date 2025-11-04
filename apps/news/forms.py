"""
Forms for news app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import NewsPost, NewsCategory


class NewsPostForm(forms.ModelForm):
    """Form for creating/editing news posts."""
    
    class Meta:
        model = NewsPost
        fields = [
            "title",
            "excerpt",
            "content",
            "category",
            "category_type",
            "visibility",
            "featured_image",
            "is_published",
            "published_at",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Enter post title"),
            }),
            "excerpt": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Brief summary (optional)"),
            }),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 15,
                "placeholder": _("Post content"),
            }),
            "category": forms.Select(attrs={"class": "form-control"}),
            "category_type": forms.Select(attrs={"class": "form-control"}),
            "visibility": forms.Select(attrs={"class": "form-control"}),
            "featured_image": forms.FileInput(attrs={"class": "form-control"}),
            "published_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        # Ensure category queryset includes all categories with empty option
        self.fields["category"].queryset = NewsCategory.objects.all().order_by("name")
        self.fields["category"].empty_label = _("Select a category (optional)")
        self.fields["category"].required = False
        
        if user and not (user.is_admin() or user.is_board_member()):
            # Regular members can't publish directly - remove these fields
            if "is_published" in self.fields:
                del self.fields["is_published"]
            if "published_at" in self.fields:
                del self.fields["published_at"]


class NewsCategoryForm(forms.ModelForm):
    """Form for creating/editing news categories."""
    
    class Meta:
        model = NewsCategory
        fields = ["name", "slug", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Category name"),
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("category-slug"),
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Category description (optional)"),
            }),
        }


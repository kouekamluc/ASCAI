"""
Forms for forums app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from ckeditor.widgets import CKEditorWidget
from .models import Thread, Reply, Flag


class ThreadForm(forms.ModelForm):
    """Form for creating/editing threads."""
    
    content = forms.CharField(
        widget=CKEditorWidget(config_name="default"),
        label=_("Content")
    )
    
    class Meta:
        model = Thread
        fields = ["title", "content", "category", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Enter thread title"),
            }),
            "category": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("tags, separated, by, commas"),
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        # Hide category field when editing (instance exists)
        if self.instance and self.instance.pk:
            self.fields.pop("category", None)
        else:
            # Only show active categories
            self.fields["category"].queryset = self.fields["category"].queryset.filter(is_active=True)
            
            # Check if user can post in categories and filter accordingly
            if user and user.is_authenticated:
                accessible_categories = [
                    cat for cat in self.fields["category"].queryset
                    if cat.can_user_post(user)
                ]
                self.fields["category"].queryset = self.fields["category"].queryset.filter(
                    pk__in=[cat.pk for cat in accessible_categories]
                )


class ReplyForm(forms.ModelForm):
    """Form for creating/editing replies."""
    
    content = forms.CharField(
        widget=CKEditorWidget(config_name="default"),
        label=_("Content")
    )
    
    class Meta:
        model = Reply
        fields = ["content", "parent_reply"]
        widgets = {
            "parent_reply": forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        thread = kwargs.pop("thread", None)
        super().__init__(*args, **kwargs)
        
        # If editing, hide parent_reply field
        if self.instance and self.instance.pk:
            self.fields["parent_reply"].widget = forms.HiddenInput()
        else:
            # For new replies, allow selecting parent reply
            if thread:
                self.fields["parent_reply"].queryset = thread.replies.filter(is_approved=True)
                self.fields["parent_reply"].widget = forms.Select(attrs={
                    "class": "form-control",
                })


class FlagForm(forms.ModelForm):
    """Form for flagging content."""
    
    class Meta:
        model = Flag
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={
                "class": "form-control",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Please provide additional details (optional)"),
            }),
        }
        labels = {
            "reason": _("Reason for reporting"),
            "description": _("Additional details"),
        }


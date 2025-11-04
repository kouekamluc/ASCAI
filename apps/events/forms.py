"""
Forms for events app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Event, EventCategory, EventRegistration


class EventForm(forms.ModelForm):
    """Form for creating/editing events."""
    
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "start_date",
            "end_date",
            "category",
            "organizer",
            "is_registration_required",
            "max_attendees",
            "registration_deadline",
            "visibility",
            "featured_image",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Enter event title"),
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": _("Event description"),
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Event location"),
            }),
            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "end_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "organizer": forms.Select(attrs={"class": "form-control"}),
            "max_attendees": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": _("Leave empty for unlimited"),
            }),
            "registration_deadline": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "visibility": forms.Select(attrs={"class": "form-control"}),
            "featured_image": forms.FileInput(attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        
        # Ensure category queryset includes all categories with empty option
        self.fields["category"].queryset = EventCategory.objects.all().order_by("name")
        self.fields["category"].empty_label = _("Select a category (optional)")
        self.fields["category"].required = False
        
        # Set organizer to current user if creating new event
        if user and not self.instance.pk:
            self.fields["organizer"].initial = user
        
        # If user is not admin, only allow them to be organizer
        if user and not user.is_admin():
            self.fields["organizer"].queryset = Event._meta.get_field("organizer").related_model.objects.filter(id=user.id)
            self.fields["organizer"].widget.attrs["readonly"] = True
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        registration_deadline = cleaned_data.get("registration_deadline")
        
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError(_("End date must be after start date."))
        
        if registration_deadline and start_date:
            if registration_deadline > start_date:
                raise forms.ValidationError(_("Registration deadline must be before event start date."))
        
        return cleaned_data


class EventFilterForm(forms.Form):
    """Form for filtering events."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Search events..."),
        }),
    )
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date_from = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        ),
    )
    date_to = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        ),
    )
    visibility = forms.ChoiceField(
        choices=[("", _("All"))] + list(Event.Visibility.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class RegistrationForm(forms.ModelForm):
    """Form for event registration/RSVP."""
    
    class Meta:
        model = EventRegistration
        fields = [
            "dietary_requirements",
            "special_requests",
        ]
        widgets = {
            "dietary_requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Any dietary requirements or restrictions"),
            }),
            "special_requests": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Any special requests or accommodations needed"),
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event", None)
        super().__init__(*args, **kwargs)


class RegistrationAdminForm(forms.ModelForm):
    """Admin form for managing registrations."""
    
    class Meta:
        model = EventRegistration
        fields = [
            "user",
            "event",
            "status",
            "dietary_requirements",
            "special_requests",
            "admin_notes",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "form-control"}),
            "event": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "dietary_requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "special_requests": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "admin_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
        }


class EventCategoryForm(forms.ModelForm):
    """Form for creating/editing event categories."""
    
    class Meta:
        model = EventCategory
        fields = ["name", "slug", "description", "color"]
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
            "color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color",
            }),
        }

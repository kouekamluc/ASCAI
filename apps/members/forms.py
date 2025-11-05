"""
Member forms for ASCAI platform.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Member, MemberApplication


class MemberProfileForm(forms.ModelForm):
    """Form for members to edit their own profile (basic fields only)."""

    class Meta:
        model = Member
        fields = [
            # Academic information
            "university",
            "course",
            "year_of_study",
            "graduation_year",
            # Personal information
            "city",
            "country_of_origin",
            "date_of_birth",
            # Privacy settings
            "profile_public",
            "email_public",
            # Links
            "linkedin",
            "website",
        ]
        widgets = {
            "university": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("University name")}
            ),
            "course": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Course of study"),
                }
            ),
            "year_of_study": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 10,
                    "placeholder": _("Year of study"),
                }
            ),
            "graduation_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1900,
                    "max": 2100,
                    "placeholder": _("Graduation year"),
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("City")}
            ),
            "country_of_origin": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Country of origin"),
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "profile_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "email_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "linkedin": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://linkedin.com/in/username",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://yourwebsite.com",
                }
            ),
        }
        help_texts = {
            "university": _("The university you are attending or attended."),
            "course": _("Your field of study or degree program."),
            "year_of_study": _("Current year of study (1-10)."),
            "graduation_year": _("Year you graduated or expect to graduate."),
            "profile_public": _("Allow other members to view your profile."),
            "email_public": _("Allow other members to see your email address."),
            "linkedin": _("Your LinkedIn profile URL."),
            "website": _("Your personal or professional website URL."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional but add required visual indicator for important fields
        for field in self.fields:
            self.fields[field].required = False


class MemberAdminForm(forms.ModelForm):
    """Form for admin/board members to edit advanced member fields."""

    class Meta:
        model = Member
        fields = [
            # Membership management
            "membership_number",
            "status",
            "category",
            "membership_expiry",
            # Verification
            "is_verified",
        ]
        widgets = {
            "membership_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Unique membership number"),
                }
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "membership_expiry": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "is_verified": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "membership_number": _("Unique membership identifier."),
            "status": _("Current membership status."),
            "category": _("Member category (Student, Alumni, Honorary)."),
            "membership_expiry": _("Date when membership expires."),
            "is_verified": _("Mark member as verified by association."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Membership number is optional but should be unique
        self.fields["membership_number"].required = False


class MemberApplicationForm(forms.ModelForm):
    """Form for users to apply for membership."""

    class Meta:
        model = MemberApplication
        fields = ["notes"]
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _(
                        "Tell us why you'd like to become a member of ASCAI..."
                    ),
                }
            ),
        }
        help_texts = {
            "notes": _(
                "Optional: Share any additional information about yourself or why you'd like to join."
            ),
        }


class MemberApplicationReviewForm(forms.ModelForm):
    """Form for admin/board to review member applications."""

    class Meta:
        model = MemberApplication
        fields = ["status", "review_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "review_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Internal review notes (visible to applicant if rejected)"),
                }
            ),
        }


"""
Forms for jobs app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import JobPosting, JobApplication


class JobPostingForm(forms.ModelForm):
    """Form for creating/editing job postings."""

    class Meta:
        model = JobPosting
        fields = [
            "title",
            "company_name",
            "location",
            "job_type",
            "salary_min",
            "salary_max",
            "description",
            "requirements",
            "deadline",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter job title"),
                }
            ),
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter company name"),
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter location (e.g., Rome, Italy)"),
                }
            ),
            "job_type": forms.Select(attrs={"class": "form-control"}),
            "salary_min": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Minimum salary (optional)"),
                    "step": "0.01",
                }
            ),
            "salary_max": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Maximum salary (optional)"),
                    "step": "0.01",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": _("Job description"),
                }
            ),
            "requirements": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Job requirements (optional)"),
                }
            ),
            "deadline": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
        }

    def clean_deadline(self):
        """Validate that deadline is in the future if provided."""
        deadline = self.cleaned_data.get("deadline")
        if deadline and deadline <= timezone.now():
            raise ValidationError(_("Deadline must be in the future."))
        return deadline

    def clean(self):
        """Validate salary range."""
        cleaned_data = super().clean()
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError(
                _("Minimum salary cannot be greater than maximum salary.")
            )

        return cleaned_data


class JobApplicationForm(forms.ModelForm):
    """Form for applying to jobs with resume upload."""

    class Meta:
        model = JobApplication
        fields = ["cover_letter", "resume"]
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": _("Your cover letter (optional)"),
                }
            ),
            "resume": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

    def clean_resume(self):
        """Validate resume file type and size."""
        resume = self.cleaned_data.get("resume")
        if not resume:
            raise ValidationError(_("Resume is required."))

        # Check file extension
        allowed_extensions = [".pdf", ".doc", ".docx"]
        file_name = resume.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                _("Only PDF, DOC, and DOCX files are allowed.")
            )

        # Check file size (10MB max from settings)
        max_size = 10 * 1024 * 1024  # 10MB
        if resume.size > max_size:
            raise ValidationError(
                _("File size cannot exceed 10MB.")
            )

        return resume












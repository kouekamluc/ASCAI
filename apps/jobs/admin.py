"""
Admin configuration for jobs app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import JobPosting, JobApplication


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    """Admin interface for JobPosting model."""

    list_display = [
        "title",
        "company_name",
        "location",
        "job_type",
        "posted_by",
        "posted_at",
        "deadline",
        "is_active",
        "views_count",
        "get_application_count",
    ]
    list_filter = [
        "job_type",
        "location",
        "is_active",
        "posted_at",
    ]
    search_fields = [
        "title",
        "company_name",
        "description",
        "location",
    ]
    readonly_fields = ["posted_at", "views_count"]
    date_hierarchy = "posted_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "posted_by",
                )
            },
        ),
        (
            _("Job Information"),
            {
                "fields": (
                    "company_name",
                    "location",
                    "job_type",
                    "description",
                    "requirements",
                )
            },
        ),
        (
            _("Salary & Deadline"),
            {
                "fields": (
                    "salary_min",
                    "salary_max",
                    "deadline",
                )
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_active",
                    "posted_at",
                    "views_count",
                )
            },
        ),
    )

    def get_application_count(self, obj):
        """Display application count."""
        return obj.get_application_count()

    get_application_count.short_description = _("Applications")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """Admin interface for JobApplication model."""

    list_display = [
        "applicant",
        "job",
        "status",
        "applied_at",
        "reviewed_at",
    ]
    list_filter = [
        "status",
        "applied_at",
        "reviewed_at",
        "job",
    ]
    search_fields = [
        "applicant__first_name",
        "applicant__last_name",
        "applicant__email",
        "job__title",
        "job__company_name",
    ]
    readonly_fields = ["applied_at", "reviewed_at"]
    date_hierarchy = "applied_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "job",
                    "applicant",
                    "status",
                )
            },
        ),
        (
            _("Application Details"),
            {
                "fields": (
                    "cover_letter",
                    "resume",
                )
            },
        ),
        (
            _("Review Information"),
            {
                "fields": (
                    "notes",
                    "applied_at",
                    "reviewed_at",
                )
            },
        ),
    )

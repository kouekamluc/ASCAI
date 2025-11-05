"""
Job and internship board models for ASCAI platform.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class JobPosting(models.Model):
    """Job or internship posting model."""

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", _("Full Time")
        PART_TIME = "part_time", _("Part Time")
        INTERNSHIP = "internship", _("Internship")
        CONTRACT = "contract", _("Contract")
        TEMPORARY = "temporary", _("Temporary")

    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(_("description"))
    company_name = models.CharField(_("company name"), max_length=200)
    location = models.CharField(_("location"), max_length=200)
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.FULL_TIME,
    )
    salary_min = models.DecimalField(
        _("minimum salary"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Minimum salary (optional)"),
    )
    salary_max = models.DecimalField(
        _("maximum salary"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Maximum salary (optional)"),
    )
    requirements = models.TextField(_("requirements"), blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_postings",
        verbose_name=_("posted by"),
    )
    posted_at = models.DateTimeField(_("posted at"), auto_now_add=True)
    deadline = models.DateTimeField(_("application deadline"), null=True, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    views_count = models.PositiveIntegerField(_("views"), default=0)

    class Meta:
        verbose_name = _("job posting")
        verbose_name_plural = _("job postings")
        ordering = ["-posted_at"]
        indexes = [
            models.Index(fields=["-posted_at"]),
            models.Index(fields=["job_type"]),
            models.Index(fields=["location"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_active", "posted_at"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("jobs:detail", kwargs={"slug": self.slug})

    def can_apply(self):
        """Check if job is still accepting applications."""
        if not self.is_active:
            return False
        if self.deadline and timezone.now() > self.deadline:
            return False
        return True

    def get_application_count(self):
        """Get total number of applications for this job."""
        return self.applications.count()


class JobApplication(models.Model):
    """Job application model."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        REVIEWED = "reviewed", _("Under Review")
        ACCEPTED = "accepted", _("Accepted")
        REJECTED = "rejected", _("Rejected")

    job = models.ForeignKey(
        JobPosting,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("job"),
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
        verbose_name=_("applicant"),
    )
    cover_letter = models.TextField(_("cover letter"), blank=True)
    resume = models.FileField(
        _("resume"),
        upload_to="resumes/",
        help_text=_("Upload your resume (PDF, DOC, or DOCX, max 10MB)"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    applied_at = models.DateTimeField(_("applied at"), auto_now_add=True)
    reviewed_at = models.DateTimeField(_("reviewed at"), null=True, blank=True)
    notes = models.TextField(
        _("notes"),
        blank=True,
        help_text=_("Internal notes for the employer"),
    )

    class Meta:
        verbose_name = _("job application")
        verbose_name_plural = _("job applications")
        ordering = ["-applied_at"]
        unique_together = [["job", "applicant"]]
        indexes = [
            models.Index(fields=["-applied_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.applicant.full_name} - {self.job.title}"

    def get_resume_url(self):
        """Get the URL of the resume file."""
        if self.resume:
            return self.resume.url
        return None

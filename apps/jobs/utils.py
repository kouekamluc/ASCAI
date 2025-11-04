"""
Utility functions for jobs app.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _


def send_application_confirmation(application):
    """Send confirmation email to applicant after applying."""
    subject = _("Application Submitted - {job_title}").format(
        job_title=application.job.title
    )
    message = render_to_string(
        "jobs/emails/application_submitted.html",
        {
            "application": application,
            "job": application.job,
            "applicant": application.applicant,
        },
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [application.applicant.email],
        html_message=message,
        fail_silently=False,
    )


def send_new_application_notification(job, application):
    """Send notification email to job poster when someone applies."""
    subject = _("New Application for {job_title}").format(job_title=job.title)
    message = render_to_string(
        "jobs/emails/new_application_notification.html",
        {
            "job": job,
            "application": application,
            "applicant": application.applicant,
            "poster": job.posted_by,
        },
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [job.posted_by.email],
        html_message=message,
        fail_silently=False,
    )


def send_status_update_notification(application, old_status):
    """Send email to applicant when application status changes."""
    if application.status == old_status:
        return  # No change, don't send email

    subject = _("Application Status Update - {job_title}").format(
        job_title=application.job.title
    )
    message = render_to_string(
        "jobs/emails/status_update.html",
        {
            "application": application,
            "job": application.job,
            "applicant": application.applicant,
            "old_status": old_status,
        },
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [application.applicant.email],
        html_message=message,
        fail_silently=False,
    )


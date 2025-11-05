"""
Views for jobs app.
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import JobPosting, JobApplication
from .forms import JobPostingForm, JobApplicationForm
from .utils import (
    send_application_confirmation,
    send_new_application_notification,
    send_status_update_notification,
)


def job_list(request):
    """List all active job postings with filtering and search."""
    jobs = JobPosting.objects.filter(is_active=True).select_related('posted_by')

    # Filter by job type
    job_type = request.GET.get("job_type")
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # Filter by location
    location = request.GET.get("location")
    if location:
        jobs = jobs.filter(location__icontains=location)

    # Filter by company
    company = request.GET.get("company")
    if company:
        jobs = jobs.filter(company_name__icontains=company)

    # Filter by salary range
    salary_min = request.GET.get("salary_min")
    if salary_min:
        try:
            salary_min = float(salary_min)
            jobs = jobs.filter(
                Q(salary_max__gte=salary_min) | Q(salary_max__isnull=True),
                salary_min__lte=salary_min,
            ) | jobs.filter(salary_min__gte=salary_min)
        except ValueError:
            pass

    # Filter by date posted
    date_from = request.GET.get("date_from")
    if date_from:
        try:
            from datetime import datetime

            date_from = datetime.strptime(date_from, "%Y-%m-%d")
            jobs = jobs.filter(posted_at__gte=date_from)
        except ValueError:
            pass

    # Search
    search_query = request.GET.get("search")
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(company_name__icontains=search_query)
            | Q(requirements__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "job_type_choices": JobPosting.JobType.choices,
        "search_query": search_query,
        "job_type": job_type,
        "location": location,
        "company": company,
        "salary_min": salary_min,
        "date_from": date_from,
    }

    return render(request, "jobs/list.html", context)


def job_detail(request, slug):
    """Detail view for a job posting."""
    job = get_object_or_404(JobPosting, slug=slug)

    # Increment views
    job.views_count += 1
    job.save(update_fields=["views_count"])

    # Check if user has already applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(
            job=job, applicant=request.user
        ).exists()

    # Get application count
    application_count = job.get_application_count()

    context = {
        "job": job,
        "has_applied": has_applied,
        "can_apply": job.can_apply(),
        "application_count": application_count,
    }

    return render(request, "jobs/detail.html", context)


@login_required
def job_create(request):
    """Create a new job posting."""
    if request.method == "POST":
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user

            # Generate slug from title
            base_slug = slugify(job.title)
            slug = base_slug
            counter = 1
            while JobPosting.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            job.slug = slug

            job.save()
            messages.success(request, _("Job posting created successfully."))
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = JobPostingForm()

    return render(request, "jobs/form.html", {"form": form, "action": _("Create")})


@login_required
def job_edit(request, slug):
    """Edit an existing job posting."""
    job = get_object_or_404(JobPosting, slug=slug)

    # Check permission
    if job.posted_by != request.user and not request.user.is_admin():
        messages.error(request, _("You can only edit your own job postings."))
        return redirect("jobs:detail", slug=job.slug)

    if request.method == "POST":
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, _("Job posting updated successfully."))
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = JobPostingForm(instance=job)

    return render(
        request,
        "jobs/form.html",
        {"form": form, "job": job, "action": _("Edit")},
    )


@login_required
def job_delete(request, slug):
    """Delete a job posting."""
    job = get_object_or_404(JobPosting, slug=slug)

    # Check permission
    if job.posted_by != request.user and not request.user.is_admin():
        messages.error(request, _("You can only delete your own job postings."))
        return redirect("jobs:detail", slug=job.slug)

    if request.method == "POST":
        job.delete()
        messages.success(request, _("Job posting deleted successfully."))
        return redirect("jobs:list")

    return render(request, "jobs/delete_confirm.html", {"job": job})


@login_required
def job_apply(request, slug):
    """Apply to a job posting."""
    job = get_object_or_404(JobPosting, slug=slug)

    # Check if job is still accepting applications
    if not job.can_apply():
        messages.error(request, _("This job is no longer accepting applications."))
        return redirect("jobs:detail", slug=job.slug)

    # Check if user has already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, _("You have already applied to this job."))
        return redirect("jobs:detail", slug=job.slug)

    # Don't allow applying to own job
    if job.posted_by == request.user:
        messages.error(request, _("You cannot apply to your own job posting."))
        return redirect("jobs:detail", slug=job.slug)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()

            # Send email notifications
            send_application_confirmation(application)
            send_new_application_notification(job, application)

            messages.success(
                request, _("Your application has been submitted successfully.")
            )
            return redirect("jobs:application_detail", pk=application.pk)
    else:
        form = JobApplicationForm()

    context = {"form": form, "job": job}
    return render(request, "jobs/apply.html", context)


@login_required
def my_applications(request):
    """View user's applications."""
    applications = JobApplication.objects.filter(applicant=request.user)

    # Filter by status
    status = request.GET.get("status")
    if status:
        applications = applications.filter(status=status)

    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status_choices": JobApplication.Status.choices,
        "status": status,
    }

    return render(request, "jobs/applications_list.html", context)


@login_required
def application_detail(request, pk):
    """View application details."""
    application = get_object_or_404(JobApplication, pk=pk)

    # Check permission - applicant or job poster
    if (
        application.applicant != request.user
        and application.job.posted_by != request.user
        and not request.user.is_admin()
    ):
        messages.error(request, _("You don't have permission to view this application."))
        return redirect("jobs:list")

    context = {"application": application}
    return render(request, "jobs/application_detail.html", context)


@login_required
def my_postings(request):
    """View jobs posted by user."""
    jobs = JobPosting.objects.filter(posted_by=request.user)

    # Filter by active status
    is_active = request.GET.get("is_active")
    if is_active is not None:
        is_active = is_active.lower() == "true"
        jobs = jobs.filter(is_active=is_active)

    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "is_active": is_active}
    return render(request, "jobs/my_postings.html", context)


@login_required
def manage_applications(request, slug):
    """Manage applications for a specific job."""
    job = get_object_or_404(JobPosting, slug=slug)

    # Check permission - only job poster or admin
    if job.posted_by != request.user and not request.user.is_admin():
        messages.error(
            request, _("You can only manage applications for your own job postings.")
        )
        return redirect("jobs:detail", slug=job.slug)

    applications = JobApplication.objects.filter(job=job)

    # Filter by status
    status = request.GET.get("status")
    if status:
        applications = applications.filter(status=status)

    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "job": job,
        "page_obj": page_obj,
        "status_choices": JobApplication.Status.choices,
        "status": status,
    }

    return render(request, "jobs/manage_applications.html", context)


@login_required
def update_application_status(request, pk):
    """Update application status."""
    application = get_object_or_404(JobApplication, pk=pk)

    # Check permission - only job poster or admin
    if (
        application.job.posted_by != request.user
        and not request.user.is_admin()
    ):
        messages.error(
            request, _("You don't have permission to update this application.")
        )
        return redirect("jobs:application_detail", pk=application.pk)

    if request.method == "POST":
        old_status = application.status
        new_status = request.POST.get("status")

        if new_status in dict(JobApplication.Status.choices):
            application.status = new_status
            if new_status != JobApplication.Status.PENDING:
                application.reviewed_at = timezone.now()
            application.save()

            # Send email notification
            send_status_update_notification(application, old_status)

            messages.success(request, _("Application status updated successfully."))
            return redirect("jobs:manage_applications", slug=application.job.slug)
        else:
            messages.error(request, _("Invalid status selected."))

    return redirect("jobs:application_detail", pk=application.pk)

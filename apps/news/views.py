"""
Views for news app.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from .models import NewsPost, NewsCategory
from .forms import NewsPostForm, NewsCategoryForm


def news_list(request):
    """List all published news posts."""
    posts = NewsPost.objects.filter(is_published=True)
    
    # Filter by visibility
    if request.user.is_authenticated:
        if request.user.is_board_member():
            pass  # Board members can see all
        elif request.user.is_member():
            posts = posts.exclude(visibility=NewsPost.Visibility.BOARD_ONLY)
        else:
            posts = posts.filter(visibility=NewsPost.Visibility.PUBLIC)
    else:
        posts = posts.filter(visibility=NewsPost.Visibility.PUBLIC)
    
    # Filter by category
    category_slug = request.GET.get("category")
    if category_slug:
        category = get_object_or_404(NewsCategory, slug=category_slug)
        posts = posts.filter(category=category)
    
    # Search
    search_query = request.GET.get("search")
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # Filter by category type
    category_type = request.GET.get("type")
    if category_type:
        posts = posts.filter(category_type=category_type)
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "categories": NewsCategory.objects.all(),
        "category_choices": NewsPost.Category.choices,
        "search_query": search_query,
        "category_slug": category_slug,
        "category_type": category_type,
    }
    
    return render(request, "news/list.html", context)


def news_detail(request, slug):
    """Detail view for a news post."""
    post = get_object_or_404(NewsPost, slug=slug)
    
    # Check visibility
    if not post.can_view(request.user):
        messages.error(request, _("You don't have permission to view this post."))
        return redirect("news:list")
    
    # Increment views
    post.views_count += 1
    post.save(update_fields=["views_count"])
    
    # Related posts
    related_posts = NewsPost.objects.filter(
        category=post.category,
        is_published=True,
    ).exclude(id=post.id)[:3]
    
    context = {
        "post": post,
        "related_posts": related_posts,
    }
    
    return render(request, "news/detail.html", context)


@login_required
@user_passes_test(lambda u: u.is_board_member())
def news_create(request):
    """Create a new news post."""
    if request.method == "POST":
        form = NewsPostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            # Generate slug from title
            if not post.slug:
                base_slug = slugify(post.title)
                slug = base_slug
                counter = 1
                while NewsPost.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                post.slug = slug
            
            if not post.published_at and post.is_published:
                post.published_at = timezone.now()
            post.save()
            messages.success(request, _("News post created successfully."))
            return redirect("news:detail", slug=post.slug)
    else:
        form = NewsPostForm(user=request.user)
    
    return render(request, "news/form.html", {"form": form, "action": _("Create")})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def news_edit(request, slug):
    """Edit an existing news post."""
    post = get_object_or_404(NewsPost, slug=slug)
    
    # Check permission
    if post.author != request.user and not request.user.is_admin():
        messages.error(request, _("You can only edit your own posts."))
        return redirect("news:detail", slug=post.slug)
    
    if request.method == "POST":
        form = NewsPostForm(
            request.POST,
            request.FILES,
            instance=post,
            user=request.user,
        )
        if form.is_valid():
            post = form.save(commit=False)
            if not post.published_at and post.is_published:
                post.published_at = timezone.now()
            post.save()
            messages.success(request, _("News post updated successfully."))
            return redirect("news:detail", slug=post.slug)
    else:
        form = NewsPostForm(instance=post, user=request.user)
    
    return render(request, "news/form.html", {
        "form": form,
        "post": post,
        "action": _("Edit"),
    })


@login_required
@user_passes_test(lambda u: u.is_board_member())
def news_delete(request, slug):
    """Delete a news post."""
    post = get_object_or_404(NewsPost, slug=slug)
    
    # Check permission
    if post.author != request.user and not request.user.is_admin():
        messages.error(request, _("You can only delete your own posts."))
        return redirect("news:detail", slug=post.slug)
    
    if request.method == "POST":
        post.delete()
        messages.success(request, _("News post deleted successfully."))
        return redirect("news:list")
    
    return render(request, "news/delete_confirm.html", {"post": post})


# Category Management Views
@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_list(request):
    """List all news categories."""
    categories = NewsCategory.objects.all().order_by("name")
    return render(request, "news/category_list.html", {"categories": categories})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_create(request):
    """Create a new news category."""
    if request.method == "POST":
        form = NewsCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if not category.slug:
                base_slug = slugify(category.name)
                slug = base_slug
                counter = 1
                while NewsCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                category.slug = slug
            category.save()
            messages.success(request, _("Category created successfully."))
            return redirect("news:category_list")
    else:
        form = NewsCategoryForm()
    
    return render(request, "news/category_form.html", {"form": form, "action": _("Create")})


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_edit(request, pk):
    """Edit an existing news category."""
    category = get_object_or_404(NewsCategory, pk=pk)
    
    if request.method == "POST":
        form = NewsCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category updated successfully."))
            return redirect("news:category_list")
    else:
        form = NewsCategoryForm(instance=category)
    
    return render(request, "news/category_form.html", {
        "form": form,
        "category": category,
        "action": _("Edit"),
    })


@login_required
@user_passes_test(lambda u: u.is_board_member())
def category_delete(request, pk):
    """Delete a news category."""
    category = get_object_or_404(NewsCategory, pk=pk)
    
    # Check if category is used by any posts
    post_count = category.posts.count()
    
    if request.method == "POST":
        if post_count > 0:
            messages.error(
                request,
                _("Cannot delete category. It is used by %(count)s post(s).") % {"count": post_count}
            )
        else:
            category.delete()
            messages.success(request, _("Category deleted successfully."))
        return redirect("news:category_list")
    
    return render(request, "news/category_delete_confirm.html", {
        "category": category,
        "post_count": post_count,
    })

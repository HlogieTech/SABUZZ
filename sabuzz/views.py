# sabuzz/views.py
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import UserProfileForm, JournalistProfileForm, AdminProfileForm, ProfileForm
from .models import Profile
from django.http import JsonResponse
from django.conf import settings
from .forms import CustomRegisterForm, LoginForm
from .models import (
    Post, Category, Comment, Subscriber,
    Favorite, SavedArticle, SavedPost, JournalistRequest, Like, Activity
)

# Optional serializer (API)
try:
    from sabuzz.api.serializers import PostSerializer
except Exception:
    PostSerializer = None

API_KEY = "pub_5741e9332f0f408186a23f2be286c5f5"


# -------------------------
# Helpers
# -------------------------
def is_journalist(user):
    """Return True if user is superuser or in 'Journalists' group."""
    return bool(
        user and user.is_authenticated and
        (user.is_superuser or user.groups.filter(name="Journalists").exists())
    )


# -------------------------
# Static / home
# -------------------------
def about(request):
    return render(request, "sabuzz/about.html")


def contact(request):
    return render(request, "sabuzz/contact.html")


def home(request):
    """
    Show API articles (newsdata.io) + local published posts.
    """
    url = f"https://newsdata.io/api/1/news?country=za&apikey={API_KEY}"
    articles = []
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            articles = r.json().get("results", [])
    except Exception:
        articles = []

    local_posts = Post.objects.filter(status="published").order_by("-created_at")[:10]

    profile = None
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = None

    return render(request, "sabuzz/index.html", {"articles": articles, "local_posts": local_posts, "profile": profile, })


# -------------------------
# Weather widget (small)
# -------------------------
def weather_widget(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    api_key= settings.OPENWEATHER_API_KEY

    if not api_key:
        return JsonResponse ({"error": "Missing API key"}, status = 400)

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
    
    r = requests.get(url).json()

    return JsonResponse({
        "city": r.get("name"),
        "temperature": r["main"]["temp"] if "main" in r else None,
    })



# -------------------------
# Auth: login / logout
# -------------------------
def login_user(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
 
        if form.is_valid():
            user = form.get_user()
 
            # Check pending journalist application
            pending_request = JournalistRequest.objects.filter(
                user=user, status="pending"
            ).first()
 
            if pending_request:
                messages.warning(
                    request,
                    "Your journalist application is still pending approval."
                )
                return render(
                    request,
                    "sabuzz/login.html",
                    {"form": form, "pending_request": True},
                )
 
            # Log in user
            login(request, user)
 
            # SUPERUSER → dashboard
            if user.is_superuser:
                return redirect("dashboard")
 
            # JOURNALIST → dashboard (using your helper)
            if is_journalist(user):
                return redirect("dashboard")
 
            # NORMAL USER → home
            return redirect("home")
 
        else:
            messages.error(request, "Incorrect username or password.")
 
    else:
        form = LoginForm()
 
    return render(request, "sabuzz/login.html", {"form": form})
 
"""
Manual password reset view.
GET: Show reset form
POST: Process password reset
"""

def manual_reset(request):
    if request.method == "POST":
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "sabuzz/manual_reset.html")

        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            return redirect("login")
        except User.DoesNotExist:
            messages.error(request, "Username does not exist.")
            return render(request, "sabuzz/manual_reset.html")
        
    return render(request, "sabuzz/manual_reset.html")

def logout_user(request):
    logout(request)
    return redirect("home")


# -------------------------
# Register
# -------------------------
def register_user(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data.get("email", "")
            user.save()

            account_type = form.cleaned_data.get("account_type")
            reason = form.cleaned_data.get("reason")
            if account_type == "journalist":
                JournalistRequest.objects.create(user=user, reason=reason or "")
                messages.info(request, "Your journalist application is pending approval.")
            else:
                messages.success(request, "Account created! You may now log in.")
            return redirect("login")
    else:
        form = CustomRegisterForm()
    return render(request, "sabuzz/register.html", {"form": form})


# -------------------------
# POSTS (Journalist CRUD)
# -------------------------
@login_required
def edit_post(request, post_id):
    # Get the post or 404
    post = get_object_or_404(Post, id=post_id)
 
    # Permission: journalists can only edit their own posts
    if not request.user.is_superuser and post.author != request.user:
        messages.error(request, "You do not have permission to edit this post.")
        return redirect("dashboard")
 
    categories = Category.objects.all()
 
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category_id = request.POST.get("category") or None
        image = request.FILES.get("image")
        action = request.POST.get("action")  # "draft" or "submit"
        status = "pending" if action == "submit" else "draft"
 
        if not title or not content:
            messages.error(request, "Title and Content are required.")
            return render(request, "sabuzz/add_post.html", {
                "post": post,
                "categories": categories
            })
 
        data = {
            "title": title,
            "content": content,
            "author": request.user.id,
            "status": status,
        }
        if category_id:
            data["category"] = category_id
 
        if PostSerializer:
            serializer = PostSerializer(post, data=data, partial=True)
            if serializer.is_valid():
                saved_post = serializer.save()
                if image:
                    saved_post.image = image
                    saved_post.save()
                messages.success(
                    request,
                    "Post updated and sent for approval." if status == "pending" else "Post saved as draft."
                )
                return redirect("dashboard")
            else:
                messages.error(request, "Error updating your post. Please check your inputs.")
        else:
            # Without serializer
            post.title = title
            post.content = content
            post.status = status
            try:
                if category_id:
                    post.category = Category.objects.get(id=int(category_id))
            except Category.DoesNotExist:
                post.category = None
            if image:
                post.image = image
            post.save()
            messages.success(
                request,
                "Post updated and sent for approval." if status == "pending" else "Post saved as draft."
            )
            return redirect("dashboard")
 
    return render(request, "sabuzz/add_post.html", {
        "post": post,
        "categories": categories
    })
 
@login_required
def add_post(request):
    # Only approved journalists (or superuser) can create posts
    if not is_journalist(request.user):
        messages.error(request, "Only approved journalists can create posts.")
        return redirect("dashboard")  # redirect to dashboard instead of home
 
    categories = Category.objects.all()
 
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category_id = request.POST.get("category") or None
        image = request.FILES.get("image")
        action = request.POST.get("action")  # "draft" or "submit"
        status = "pending" if action == "submit" else "draft"
 
        # Validation
        if not title or not content:
            messages.error(request, "Title and Content are required.")
            return render(request, "sabuzz/add_post.html", {"categories": categories})
 
        data = {
            "title": title,
            "content": content,
            "author": request.user.id,
            "status": status,
        }
        if category_id:
            data["category"] = category_id
 
        if PostSerializer:
            # Use serializer if available
            serializer = PostSerializer(data=data)
            if serializer.is_valid():
                post = serializer.save()
                if image:
                    post.image = image
                    post.save()
                messages.success(
                    request,
                    "Post saved as draft." if status == "draft" else "Post submitted for approval."
                )
                return redirect("dashboard")
            else:
                messages.error(request, "Error creating post. Please check your inputs.")
        else:
            # Fallback without serializer
            post = Post(title=title, content=content, author=request.user, status=status)
            if category_id:
                try:
                    post.category = Category.objects.get(id=int(category_id))
                except Category.DoesNotExist:
                    post.category = None
            if image:
                post.image = image
            post.save()
            messages.success(
                request,
                "Post saved as draft." if status == "draft" else "Post submitted for approval."
            )
            return redirect("dashboard")

    return render(request, "sabuzz/add_post.html", {"categories": categories})

@login_required
def delete_post(request, post_id):
    # Get the post or return 404
    post = get_object_or_404(Post, id=post_id)
 
    # Only the author (journalist) or superuser can delete
    if not (request.user.is_superuser or (request.user == post.author and is_journalist(request.user))):
        return HttpResponseForbidden("You don't have permission to delete this post.")
 
    # Handle POST → actually delete
    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted successfully.")
        # Redirect to dashboard for journalists, home for others
        return redirect("dashboard" if is_journalist(request.user) else "home")
 
    # Handle GET → show confirmation page
    return render(request, "sabuzz/confirm_delete.html", {
        "object": post,
        "type": "post"
    })

# -------------------------
# Dashboard & lists (journalist)
# -------------------------
"""@user_passes_test(is_journalist)
def dashboard(request):
    posts_count = Post.objects.count()
    categories_count = Category.objects.count()
    subscribers_count = Subscriber.objects.count()
    comments_count = Comment.objects.count()
    return render(request, "sabuzz/dashboard.html", {
        "posts_count": posts_count,
        "categories_count": categories_count,
        "subscribers_count": subscribers_count,
        "comments_count": comments_count,
    })"""


@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        # Admin dashboard
        posts_count = Post.objects.count()
        categories_count = Category.objects.count()
        subscribers_count = Subscriber.objects.count()
        comments_count = Comment.objects.count()
        likes_count = Like.objects.count()
        recent_activities = Activity.objects.select_related('user', 'object').order_by('-timestamp')[:10]

        users = User.objects.all().order_by('-date_joined')
        posts = Post.objects.select_related('author', 'category').all().order_by('-created_at')
        comments = Comment.objects.select_related('user', 'post').all().order_by('-date_posted')

        return render(request, "sabuzz/dashboard.html", {
            "posts_count": posts_count,
            "categories_count": categories_count,
            "subscribers_count": subscribers_count,
            "comments_count": comments_count,
            "likes_count": likes_count,
            "recent_activities": recent_activities,
            "users": users,
            "posts": posts,
            "comments": comments,
        })

    # Journalist dashboard
    posts_count = Post.objects.filter(author=user).count()
    categories_count = Category.objects.count()
    comments_count = Comment.objects.filter(post__author=user).count()
    likes_count = Like.objects.filter(post__author=user).count()
    recent_activities = Activity.objects.filter(user=user).order_by('-timestamp')[:10]

    drafts = Post.objects.filter(author=user, status="draft").order_by('-created_at')
    pending = Post.objects.filter(author=user, status="pending").order_by('-created_at')
    published = Post.objects.filter(author=user, status="published").order_by('-created_at')

    return render(request, "sabuzz/dashboard.html", {
        "posts_count": posts_count,
        "categories_count": categories_count,
        "comments_count": comments_count,
        "likes_count": likes_count,
        "recent_activities": recent_activities,
        "drafts": drafts,
        "pending": pending,
        "published": published,
    })


# Admin user table
@user_passes_test(lambda u: u.is_superuser)
def dashboard_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, "sabuzz/dashboard_users.html", {"users": users})


# Admin post table
@user_passes_test(lambda u: u.is_superuser)
def dashboard_posts(request):
    posts = Post.objects.select_related('author', 'category').all().order_by('-created_at')
    return render(request, "sabuzz/dashboard_posts.html", {"posts": posts})


# Admin comment table
@user_passes_test(lambda u: u.is_superuser)
def dashboard_comments(request):
    comments = Comment.objects.select_related('user', 'post').all().order_by('-date_posted')
    return render(request, "sabuzz/dashboard_comments.html", {"comments": comments})


@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.username = request.POST.get("username", user.username)
        user.email = request.POST.get("email", user.email)
        user.is_active = bool(request.POST.get("is_active", True))
        user.save()
        messages.success(request, "User updated.")
        return redirect("dashboard_users")
    return render(request, "sabuzz/edit_user.html", {"user_obj": user})


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        user.delete()
        messages.success(request, "User deleted.")
    return redirect("dashboard_users")

@user_passes_test(is_journalist)
def subscribers_list(request):
    subscribers = Subscriber.objects.all().order_by("-subscribed_at")
    return render(request, "sabuzz/subscribers_list.html", {"subscribers": subscribers})


def subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            messages.error(request, "Email is required.")
            return redirect("home")
        sub, created = Subscriber.objects.get_or_create(email=email)
        if created:
            messages.success(request, "You've subscribed successfully!")
        else:
            messages.info(request, "You are already subscribed.")
        return redirect("home")


# -------------------------
# Comments management (admin)
# -------------------------
@user_passes_test(lambda u: u.is_superuser)
def comments_list(request):
    comments = Comment.objects.select_related("post", "user").order_by("-date_posted")
    return render(request, "sabuzz/comments_list.html", {"comments": comments})


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def approve_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.approved = True
    c.save()
    messages.success(request, "Comment approved.")
    return HttpResponseRedirect(request.POST.get("next", reverse("comments_list")))


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_comment_admin(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.delete()
    messages.success(request, "Comment deleted.")
    return HttpResponseRedirect(request.POST.get("next", reverse("comments_list")))


# -------------------------
# Posts approval (admin)
# -------------------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def pending_posts(request):
    posts = Post.objects.filter(status="pending").order_by("-created_at")
    return render(request, "sabuzz/pending_posts.html", {"posts": posts})


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="pending")
    post.status = "published"
    post.save()
    messages.success(request, f"Post '{post.title}' published.")
    return redirect("pending_posts")


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, status="pending")
    post.status = "draft"
    post.save()
    messages.error(request, f"Post '{post.title}' rejected (moved to draft).")
    return redirect("pending_posts")


# -------------------------
# Journalist requests (admin)
# -------------------------
@user_passes_test(lambda u: u.is_superuser)
def journalist_requests(request):
    reqs = JournalistRequest.objects.filter(status="pending")
    return render(request, "sabuzz/journalist_requests.html", {"requests": reqs})


@user_passes_test(lambda u: u.is_superuser)
def approve_journalist(request, req_id):
    req = get_object_or_404(JournalistRequest, id=req_id)
    req.status = "approved"
    req.save()
    group, _ = Group.objects.get_or_create(name="Journalists")
    req.user.groups.add(group)
    messages.success(request, f"{req.user.username} is now approved.")
    return redirect("journalist_requests")


@user_passes_test(lambda u: u.is_superuser)
def reject_journalist(request, req_id):
    req = get_object_or_404(JournalistRequest, id=req_id)
    req.status = "rejected"
    req.save()
    messages.error(request, "Journalist request rejected.")
    return redirect("journalist_requests")


# -------------------------
# Post detail + comment create
# -------------------------
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Access control for unpublished posts
    if post.status != "published":
        user_is_author = request.user.is_authenticated and (request.user == post.author)
        user_is_super = request.user.is_authenticated and request.user.is_superuser
        user_is_journalist = request.user.is_authenticated and request.user.groups.filter(name="Journalists").exists()
        if not (user_is_author or user_is_super or user_is_journalist):
            raise Http404("Post not found")

    comments = Comment.objects.filter(post=post).order_by("-date_posted")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Login required to post comments.")
            return redirect("login")

        content = request.POST.get("content", "").strip()
        if not content:
            messages.error(request, "Comment can't be empty.")
            return redirect("post_detail", post_id=post.id)

        Comment.objects.create(user=request.user, post=post, text=content, approved=False)
        messages.success(request, "Comment added (pending approval).")
        return redirect("post_detail", post_id=post.id)

    return render(request, "sabuzz/post_detail.html", {"post": post, "comments": comments})


# -------------------------
# COMMENT CRUD (normal users)
# -------------------------
@login_required
def edit_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    if request.user != c.user and not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to edit this comment.")

    if request.method == "POST":
        new_text = request.POST.get("content", "").strip()
        if not new_text:
            messages.error(request, "Comment cannot be empty.")
            return redirect("post_detail", post_id=c.post.id)
        c.text = new_text
        c.approved = False  # send edited comment back to moderation
        c.save()
        messages.success(request, "Comment updated and sent for moderation.")
        return redirect("post_detail", post_id=c.post.id)

    return render(request, "sabuzz/edit_comment.html", {"comment": c})

@login_required
@require_POST
def delete_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    if request.user != c.user and not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to delete this comment.")
    post_id = c.post.id
    c.delete()
    messages.success(request, "Comment deleted.")
    return redirect("post_detail", post_id=post_id)
    
# -------------------------
# Saved/favorites etc
# -------------------------
@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.get_or_create(user=request.user, post=post)
    return redirect("post_detail", post_id=post_id)


@login_required
def save_favorite(request):
    if request.method == "POST":
        Favorite.objects.create(
            user=request.user,
            title=request.POST.get("title"),
            link=request.POST.get("link"),
            image_url=request.POST.get("image_url"),
            source=request.POST.get("source"),
        )
    return redirect("favorites")


@login_required
def favorites(request):
    saved = Favorite.objects.filter(user=request.user).order_by("-saved_at")
    return render(request, "sabuzz/favorites.html", {"saved": saved})


@login_required
@require_POST
def remove_favorite(request, fav_id):
    fav = get_object_or_404(Favorite, id=fav_id, user=request.user)
    fav.delete()
    messages.success(request, "Removed from favorites.")
    return redirect("favorites")


@login_required
def save_article(request):
    if request.method == "POST":
        SavedArticle.objects.create(
            user=request.user,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            url=request.POST.get("url"),
            image_url=request.POST.get("image_url"),
            source_name=request.POST.get("source_name"),
        )
    return redirect("saved_articles")


@login_required
def saved_articles(request):
    saved = SavedArticle.objects.filter(user=request.user).order_by("-saved_at")
    return render(request, "sabuzz/saved_articles.html", {"saved": saved})


@login_required
@require_POST
def remove_saved_article(request, article_id):
    article = get_object_or_404(SavedArticle, id=article_id, user=request.user)
    article.delete()
    messages.success(request, "Article removed from saved list.")
    return redirect("saved_articles")


# -------------------------
# Posts page (API)
# -------------------------
def posts_page(request):
    api_url = "http://127.0.0.1:8000/api/posts/"
    try:
        response = requests.get(api_url, timeout=5)
        posts = response.json() if response.status_code == 200 else []
    except Exception:
        posts = []
    return render(request, "sabuzz/posts_page.html", {"posts": posts})


# -------------------------
# category and search
#only for API
# -------------------------
def category_news(request, category):
    url = f"https://newsdata.io/api/1/news?country=za&category={category}&apikey={API_KEY}"
    articles = []
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            articles = r.json().get("results", [])
    except Exception:
        pass
    return render(request, "sabuzz/category.html", {"category": category.capitalize(), "articles": articles})


def search_news(request):
    query = request.GET.get("q", "")
    articles = []
    if query:
        url = f"https://newsdata.io/api/1/news?q={query}&country=za&apikey={API_KEY}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                articles = r.json().get("results", [])
        except Exception:
            pass
    return render(request, "sabuzz/search.html", {"query": query, "articles": articles})

@login_required
def update_profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    # Determine which form to use based on role
    if profile.role == 'user':
        form_class = UserProfileForm
    elif profile.role == 'journalist':
        form_class = JournalistProfileForm
    else:
        form_class = AdminProfileForm

    # Handle form submission
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'sabuzz/update_profile.html', {'form': form})

#creates profile after login
@login_required
def profile_detail(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, "sabuzz/profile_detail.html", {"profile": profile})
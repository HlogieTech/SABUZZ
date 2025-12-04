# sabuzz/views.py
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CustomRegisterForm
from .models import (
    Post, Category, Comment, Subscriber,
    Favorite, SavedArticle, SavedPost, JournalistRequest
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
    return render(request, "sabuzz/index.html", {"articles": articles, "local_posts": local_posts})


# -------------------------
# Weather widget (small)
# -------------------------
def weather_widget(request):
    lat, lon = -26.2041, 28.0473
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true&timezone=Africa/Johannesburg"
    )
    weather = {}
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        current = data.get("current_weather", {})
        if current:
            weather = {
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed"),
            }
    except Exception:
        weather = None

    return render(request, "sabuzz/weather.html", {"weather": weather})


# -------------------------
# Auth: login / logout
# -------------------------
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user:
            # If user applied for journalist and request is still pending, show message instead of granting dashboard
            pending_request = JournalistRequest.objects.filter(user=user, status="pending").first()
            if pending_request:
                messages.warning(request, "Your journalist application is still pending approval.")
                # show login page with note (do not log them into dashboard)
                return render(request, "sabuzz/login.html", {"pending_request": True, "username": username})

            # If user is a journalist (approved) or superuser -> dashboard
            if is_journalist(user):
                login(request, user)
                return redirect("dashboard")

            # normal user login
            login(request, user)
            return redirect("home")

        messages.error(request, "Incorrect username or password.")

    return render(request, "sabuzz/login.html")


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
def add_post(request):
    # Only approved journalists (or superuser) can create posts
    if not is_journalist(request.user):
        messages.error(request, "Only approved journalists can create posts.")
        return redirect("home")

    categories = Category.objects.all()

    if request.method == "POST":
        # Collect data
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category_id = request.POST.get("category") or None

        data = {
            "title": title,
            "content": content,
            "author": request.user.id,
            "category": category_id,
            "status": "pending",  # journalist posts start pending for admin approval
        }

        if PostSerializer:
            serializer = PostSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                messages.success(request, "Post submitted for approval.")
                return redirect("dashboard")
            else:
                messages.error(request, "Error submitting your post. Check required fields.")
        else:
            # Fallback: create model instance directly
            post = Post(
                title=title,
                content=content,
                author=request.user,
                status="pending"
            )
            try:
                if category_id:
                    post.category = Category.objects.get(id=int(category_id))
            except Exception:
                pass
            post.save()
            messages.success(request, "Post submitted for approval.")
            return redirect("dashboard")

    return render(request, "sabuzz/add_post.html", {"categories": categories})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Allow superuser or the original author who is a journalist
    if not (request.user.is_superuser or (request.user == post.author and is_journalist(request.user))):
        return HttpResponseForbidden("You don't have permission to edit this post.")

    categories = Category.objects.all()
    if request.method == "POST":
        title = request.POST.get("title", post.title).strip()
        content = request.POST.get("content", post.content).strip()
        category_id = request.POST.get("category") or (post.category.id if post.category else None)

        data = {
            "title": title,
            "content": content,
            "author": post.author.id,
            "category": category_id,
            "status": post.status,
        }

        if PostSerializer:
            serializer = PostSerializer(post, data=data)
            if serializer.is_valid():
                serializer.save()
                messages.success(request, "Post updated.")
                return redirect("dashboard")
            else:
                messages.error(request, "Error updating post.")
        else:
            post.title = title
            post.content = content
            try:
                if category_id:
                    post.category = Category.objects.get(id=int(category_id))
            except Exception:
                pass
            post.save()
            messages.success(request, "Post updated.")
            return redirect("dashboard")

    return render(request, "sabuzz/edit_post.html", {"post": post, "categories": categories})


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not (request.user.is_superuser or (request.user == post.author and is_journalist(request.user))):
        return HttpResponseForbidden("You don't have permission to delete this post.")
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect("dashboard" if is_journalist(request.user) else "home")


# -------------------------
# Dashboard & lists (journalist)
# -------------------------
@user_passes_test(is_journalist)
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
    })


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

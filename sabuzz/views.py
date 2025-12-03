# sabuzz/views.py

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CustomRegisterForm
from .models import (
    Post, Category, Comment, Subscriber,
    Favorite, SavedArticle, SavedPost, JournalistRequest
)
from sabuzz.api.serializers import PostSerializer

API_KEY = "pub_5741e9332f0f408186a23f2be286c5f5"


# ============================================================
# JOURNALIST CHECK
# ============================================================
def is_journalist(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Journalists").exists()
    )


# ============================================================
# STATIC PAGES
# ============================================================
def home(request):
    url = f"https://newsdata.io/api/1/news?country=za&apikey={API_KEY}"
    articles = []

    try:
        response = requests.get(url, timeout=5)
        articles = response.json().get("results", [])
    except:
        pass

    return render(request, "sabuzz/index.html", {"articles": articles})


def about(request):
    return render(request, "sabuzz/about.html")


def contact(request):
    return render(request, "sabuzz/contact.html")


# ============================================================
# WEATHER PAGE
# ============================================================
def weather_widget(request):
    lat, lon = -26.2041, 28.0473
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        "&current_weather=true"
        "&daily=temperature_2m_max,temperature_2m_min,weathercode"
        "&timezone=Africa/Johannesburg"
    )

    weather = {}
    forecast = []

    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        weather = data.get("current_weather", {})
        daily = data.get("daily", {})
        forecast = zip(
            daily.get("time", []),
            daily.get("temperature_2m_min", []),
            daily.get("temperature_2m_max", []),
            daily.get("weathercode", []),
        )
    except:
        pass

    return render(request, "sabuzz/weather.html", {
        "weather": weather,
        "forecast": forecast,
    })


# ============================================================
# LOGIN / LOGOUT
# ============================================================
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if is_journalist(user):
                return redirect("dashboard")
            return redirect("home")

        messages.error(request, "Incorrect username or password.")

    return render(request, "sabuzz/login.html")


def logout_user(request):
    logout(request)
    return redirect("home")


# ============================================================
# REGISTER
# ============================================================
def register_user(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data["email"]
            user.save()

            account_type = form.cleaned_data["account_type"]
            reason = form.cleaned_data["reason"]

            if account_type == "journalist":
                JournalistRequest.objects.create(user=user, reason=reason)
                messages.info(request, "Your journalist application is pending approval.")
            else:
                messages.success(request, "Account created! You may now log in.")

            return redirect("login")

    else:
        form = CustomRegisterForm()

    return render(request, "sabuzz/register.html", {"form": form})


# ============================================================
# ADD POST
# ============================================================
@login_required
def add_post(request):
    if not is_journalist(request.user):
        messages.error(request, "Only approved journalists can create posts.")
        return redirect("home")

    categories = Category.objects.all()

    if request.method == "POST":
        data = {
            "title": request.POST.get("title"),
            "content": request.POST.get("content"),
            "author": request.user.id,
            "category": request.POST.get("category"),
            "status": "pending",
        }

        serializer = PostSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Post submitted for approval.")
            return redirect("home")

        messages.error(request, "Error submitting your post.")

    return render(request, "sabuzz/add_post.html", {"categories": categories})


# ============================================================
# DASHBOARD
# ============================================================
@user_passes_test(is_journalist)
def dashboard(request):
    return render(request, "sabuzz/dashboard.html", {
        "posts_count": Post.objects.count(),
        "categories_count": Category.objects.count(),
        "subscribers_count": Subscriber.objects.count(),
        "comments_count": Comment.objects.count(),
    })


@user_passes_test(is_journalist)
def subscribers_list(request):
    subscribers = Subscriber.objects.all().order_by("-subscribed_at")
    return render(request, "sabuzz/subscribers_list.html", {"subscribers": subscribers})


# ============================================================
# COMMENTS MANAGEMENT
# ============================================================
@user_passes_test(is_journalist)
def comments_list(request):
    comments = Comment.objects.select_related("post", "user").order_by("-date_posted")
    return render(request, "sabuzz/comments_list.html", {"comments": comments})


@user_passes_test(is_journalist)
@require_POST
def approve_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.approved = True
    c.save()
    messages.success(request, "Comment approved.")
    return HttpResponseRedirect(request.POST.get("next", reverse("comments_list")))


@user_passes_test(is_journalist)
@require_POST
def delete_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.delete()
    messages.success(request, "Comment deleted.")
    return HttpResponseRedirect(request.POST.get("next", reverse("comments_list")))


# ============================================================
# JOURNALIST REQUESTS
# ============================================================
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


# ============================================================
# POST DETAIL
# ============================================================
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by("-date_posted")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Login required.")
            return redirect("login")

        Comment.objects.create(
            user=request.user,
            post=post,
            text=request.POST.get("content")
        )
        messages.success(request, "Comment added.")
        return redirect("post_detail", post_id=post.id)

    return render(request, "sabuzz/post_detail.html", {
        "post": post,
        "comments": comments
    })


# ============================================================
# SAVED CONTENT
# ============================================================
@login_required
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    SavedPost.objects.get_or_create(user=request.user, post=post)
    return redirect("post_detail", post_id=post_id)


@login_required
def save_favorite(request):
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
    saved = SavedArticle.objects.filter(user=request.user)
    return render(request, "sabuzz/saved_articles.html", {"saved": saved})


# ============================================================
# POSTS PAGE (API)
# ============================================================
def posts_page(request):
    api_url = "http://127.0.0.1:8000/api/posts/"
    response = requests.get(api_url)
    posts = response.json()
    return render(request, "sabuzz/posts_page.html", {"posts": posts})
@user_passes_test(lambda u: u.is_superuser)
def pending_posts(request):
    posts = Post.objects.filter(status="pending").order_by("-created_at")

    return render(request, "sabuzz/pending_posts.html", {
        "posts": posts
    })


# ============================================================
# CATEGORY NEWS
# ============================================================
def category_news(request, category):
    url = f"https://newsdata.io/api/1/news?country=za&category={category}&apikey={API_KEY}"
    articles = []

    try:
        r = requests.get(url, timeout=5)
        articles = r.json().get("results", [])
    except:
        pass

    return render(request, "sabuzz/category.html", {
        "category": category.capitalize(),
        "articles": articles
    })


# ============================================================
# SEARCH NEWS
# ============================================================
def search_news(request):
    query = request.GET.get("q", "")
    articles = []

    if query:
        url = f"https://newsdata.io/api/1/news?q={query}&country=za&apikey={API_KEY}"

        try:
            r = requests.get(url, timeout=5)
            articles = r.json().get("results", [])
        except:
            pass

    return render(request, "sabuzz/search.html", {
        "query": query,
        "articles": articles
    })
@user_passes_test(lambda u: u.is_superuser)
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.status = "approved"
    post.save()
    messages.success(request, "Post approved.")
    return redirect("pending_posts")


@user_passes_test(lambda u: u.is_superuser)
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.status = "rejected"
    post.save()
    messages.error(request, "Post rejected.")
    return redirect("pending_posts")

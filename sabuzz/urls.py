# sabuzz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("weather/", views.weather_widget, name="weather_widget"),

    # Auth
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("manual-reset/", views.manual_reset, name="manual_reset"),
    path("register/", views.register_user, name="register"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/subscribers/", views.subscribers_list, name="subscribers_list"),
    path("dashboard/comments/", views.comments_list, name="comments_list"),

    # Pending posts (admin approves)
    path("dashboard/pending-posts/", views.pending_posts, name="pending_posts"),
    path("dashboard/pending-posts/<int:post_id>/approve/", views.approve_post, name="approve_post"),
    path("dashboard/pending-posts/<int:post_id>/reject/", views.reject_post, name="reject_post"),

    # Journalist requests
    path("journalist-requests/", views.journalist_requests, name="journalist_requests"),
    path("journalist-requests/<int:req_id>/approve/", views.approve_journalist, name="approve_journalist"),
    path("journalist-requests/<int:req_id>/reject/", views.reject_journalist, name="reject_journalist"),

    # Posts
    path("add-post/", views.add_post, name="add_post"),
    path("post/<int:post_id>/", views.post_detail, name="post_detail"),

    # Favorites / saved
    path("favorites/save/", views.save_favorite, name="save_favorite"),
    path("favorites/", views.favorites, name="favorites"),
    path("save-article/", views.save_article, name="save_article"),
    path("saved/", views.saved_articles, name="saved_articles"),

    # Category/search
    path("category/<str:category>/", views.category_news, name="category"),
    path("search/", views.search_news, name="search"),

    # API posts page
    path("posts/", views.posts_page, name="posts_page"),
]

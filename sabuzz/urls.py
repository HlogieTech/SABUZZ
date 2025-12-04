# sabuzz/urls.py
from django.urls import path
from . import views

urlpatterns = [

    # -------------------------
    # Public Pages
    # -------------------------
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("weather/", views.weather_widget, name="weather_widget"),

    # -------------------------
    # Auth
    # -------------------------
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),

    path("register/", views.register_user, name="register"),

    # -------------------------
    # Journalist Dashboard
    # -------------------------
    path("dashboard/", views.dashboard, name="dashboard"),
    path("add-post/", views.add_post, name="add_post"),
    path("post/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", views.delete_post, name="delete_post"),

    # -------------------------
    # Admin Post Approval
    # -------------------------
    path("dashboard/pending-posts/", views.pending_posts, name="pending_posts"),
    path("dashboard/pending-posts/<int:post_id>/approve/", views.approve_post, name="approve_post"),
    path("dashboard/pending-posts/<int:post_id>/reject/", views.reject_post, name="reject_post"),

    # -------------------------
    # Journalist Requests (Admin)
    # -------------------------
    path("journalist-requests/", views.journalist_requests, name="journalist_requests"),
    path("journalist-requests/<int:req_id>/approve/", views.approve_journalist, name="approve_journalist"),
    path("journalist-requests/<int:req_id>/reject/", views.reject_journalist, name="reject_journalist"),

    # -------------------------
    # Comments CRUD
    # -------------------------
    path("comment/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),

    # Admin comment moderation
    path("dashboard/comments/", views.comments_list, name="comments_list"),
    path("dashboard/comments/<int:comment_id>/approve/", views.approve_comment, name="approve_comment"),
    path("dashboard/comments/<int:comment_id>/delete-admin/", views.delete_comment_admin, name="delete_comment_admin"),

    # -------------------------
    # Public Post Detail
    # -------------------------
    path("post/<int:post_id>/", views.post_detail, name="post_detail"),

    # -------------------------
    # Saved Posts / Favorites
    # -------------------------
    path("post/<int:post_id>/save/", views.save_post, name="save_post"),

    path("favorites/save/", views.save_favorite, name="save_favorite"),
    path("favorites/", views.favorites, name="favorites"),

    path("save-article/", views.save_article, name="save_article"),
    path("saved/", views.saved_articles, name="saved_articles"),
# Saved articles
path("saved/remove/<int:article_id>/", views.remove_saved_article, name="remove_saved_article"),

# Favorites
path("favorites/remove/<int:fav_id>/", views.remove_favorite, name="remove_favorite"),

    # -------------------------
    # Categories & Search
    # -------------------------
    path("category/<str:category>/", views.category_news, name="category"),
    path("search/", views.search_news, name="search"),

    # -------------------------
    # API Posts Page
    # -------------------------
    path("posts/", views.posts_page, name="posts_page"),
     
     # -------------------------------------
# User CRUD – Comments (Edit/Delete)
# -------------------------------------
path("comment/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),

]

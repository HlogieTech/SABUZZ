# sabuzz/models.py
from django.db import models
from django.contrib.auth.models import User


from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL
# ============================================================
# CATEGORY
# ============================================================
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ============================================================
# LOCAL POSTS
# ============================================================
class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
        ("pending", "Pending Approval"),
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ============================================================
# COMMENTS
# ============================================================
class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment by {self.user.username}"


# ============================================================
# SUBSCRIBERS
# ============================================================
class Subscriber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Notification(models.Model):
    """
    Simple notification model — generic_text for message and optional links.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    verb = models.CharField(max_length=200)          # e.g. "Your comment was approved"
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    # Optional extras for linking to related objects
    target_post = models.ForeignKey("Post", null=True, blank=True, on_delete=models.CASCADE)
    target_comment = models.ForeignKey("Comment", null=True, blank=True, on_delete=models.CASCADE)
    extra_data = models.JSONField(null=True, blank=True)  # flexible metadata

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Notification to {self.user}: {self.verb}"

# ============================================================
# USER PROFILE
# ============================================================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    subscription_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username


# ============================================================
# LIKE SYSTEM
# ============================================================
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} likes {self.post}"


# ============================================================
# FAVORITE (API NEWS)
# ============================================================
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    link = models.URLField()
    image_url = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=200, blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# ============================================================
# SAVED API ARTICLES
# ============================================================
class SavedArticle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    url = models.URLField()
    image_url = models.URLField(blank=True, null=True)
    source_name = models.CharField(max_length=200, blank=True, null=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ============================================================
# SAVED LOCAL POSTS
# ============================================================
class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} saved {self.post.title}"


# ============================================================
# JOURNALIST APPLICATION SYSTEM
# ============================================================
class JournalistRequest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Journalist Request - {self.user.username} ({self.status})"

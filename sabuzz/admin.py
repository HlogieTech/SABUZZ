from django.contrib import admin
from .models import (
    Post, Category, Comment, Profile, Like, Subscriber,
    Notification, JournalistRequest
)

# ============================================================
# NOTIFICATIONS
# ============================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "verb", "read", "created_at")
    list_filter = ("read", "created_at")
    search_fields = ("verb", "user__username")


# ============================================================
# PROFILES (USER / JOURNALIST / ADMIN)
# ============================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'role', 'is_subscribed', 'subscription_date',
        'full_name', 'organisation', 'press_id', 'is_verified',
        'staff_id', 'admin_title'
    )
    list_filter = ('role', 'is_subscribed')
    search_fields = ('user__username', 'user__email', 'full_name', 'press_id', 'staff_id')


# ============================================================
# CATEGORY
# ============================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name',)
    ordering = ('name',)


# ============================================================
# POSTS
# ============================================================
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'author', 'category')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    ordering = ('status', 'created_at')
    list_per_page = 10


# ============================================================
# COMMENTS
# ============================================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'date_posted', 'approved')
    list_filter = ('approved', 'date_posted')
    search_fields = ('user__username', 'post__title', 'text')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"


# ============================================================
# LIKES
# ============================================================
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user')
    search_fields = ('user__username', 'post__title')


# ============================================================
# SUBSCRIBERS
# ============================================================
@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'subscribed_at')
    search_fields = ('user__username', 'email')
    list_filter = ('subscribed_at',)


# ============================================================
# JOURNALIST REQUESTS
# ============================================================
@admin.register(JournalistRequest)
class JournalistRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        for jr in queryset:
            jr.status = 'approved'
            jr.save()
            # Update Profile role to journalist
            profile, created = Profile.objects.get_or_create(user=jr.user)
            profile.role = 'journalist'
            profile.save()
    approve_requests.short_description = "Approve selected journalist requests"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
    reject_requests.short_description = "Reject selected journalist requests"

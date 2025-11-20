from django.contrib import admin
from .models import Post, Category, Comment, Profile, Like, Subscriber

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_subscribed', 'subscription_date')
    list_filter = ('role', 'is_subscribed')
    search_fields = ('user__username', 'user__email')
    
admin.site.register(Profile, ProfileAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name',)
    ordering = ('name',)

admin.site.register(Category, CategoryAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'author', 'category')
    search_fields = ('title',)
    date_hierarchy = 'created_at'
    ordering = ('status', 'created_at')
    list_per_page = 10

admin.site.register(Post, PostAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'date_posted', 'approved')
    list_filter = ('approved', 'date_posted')
    search_fields = ('user__username', 'post__title', 'text')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approved selected comments"

admin.site.register(Comment, CommentAdmin)

class LikeAdmin(admin.ModelAdmin):
    list_display =('post', 'user')
    search_fields = ('user__username', 'post__title')

admin.site.register(Like, LikeAdmin)

class SubscriberAdmin(admin.ModelAdmin):
    list_display =('user', 'email', 'subscribed_at')
    search_fields = ('user__username', 'email')
    list_filter = ('subscribed_at')

admin.site.register(Subscriber, SubscriberAdmin)
from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    ROLE_CHOICE = [
        ('admin', 'Admin'),
        ('journalist', 'Journalist'),
        ('publisher', 'Publisher'),
        ('user', 'User'),
    ]
    user =models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICE, default='user')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    subscription_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

class Category (models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Post(models.Model):
    status_choices = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_posted = models.DateField(auto_now_add=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    status = models.CharField(max_length=10, choices=status_choices, default='Draft')
    views = models.PositiveIntegerField(default=0)
    likes =models.ManyToManyField(User,related_name='liked_posts', blank=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_posted = models.DateField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class Like(models.Model):
    post = models.ForeignKey(Post, related_name='liked_posts', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"
    
class Subscriber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

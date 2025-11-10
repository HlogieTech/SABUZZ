from django.contrib import admin
from .models import Post, Category, Comment, Profile

# Register your models here.
admin.site.register(Category)

class CatergoryAdmin(admin.ModelAdmin):
list_display= ('name')
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Profile)
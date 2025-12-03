from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("sabuzz.urls")),
    path('api/', include('sabuzz.api.urls')),

]

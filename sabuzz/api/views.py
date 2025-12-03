from rest_framework import viewsets, permissions # pyright: ignore[reportMissingImports]
from rest_framework.permissions import IsAuthenticatedOrReadOnly # pyright: ignore[reportMissingImports]
from rest_framework.exceptions import PermissionDenied # pyright: ignore[reportMissingImports]
from sabuzz.models import Post
from .serializers import PostSerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only authors to edit/delete their posts.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only to the author
        return obj.author == request.user

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        # set the author to the logged-in user, force pending status
        serializer.save(author=self.request.user, status='pending')

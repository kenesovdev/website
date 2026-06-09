from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.problems.permissions import IsAdminUser
from apps.users.authentication import BearerTokenAuthentication

from .models import Post
from .serializers import PostCreateUpdateSerializer, PostDetailSerializer, PostListSerializer


class PostPagination(PageNumberPagination):
    page_size = 20


class PostListCreateView(generics.ListCreateAPIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer

    def get_queryset(self):
        qs = Post.objects.select_related('author').order_by('-created_at')
        if self.request.user.role != 'admin':
            qs = qs.filter(published=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.select_related('author')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def get_object(self):
        post = super().get_object()
        if not post.published and post.author_id != self.request.user.id and self.request.user.role != 'admin':
            raise PermissionDenied('Пост недоступен')
        return post

    def perform_update(self, serializer):
        post = self.get_object()
        if post.author_id != self.request.user.id and self.request.user.role != 'admin':
            raise PermissionDenied('Можно редактировать только свои посты')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id and self.request.user.role != 'admin':
            raise PermissionDenied('Можно удалять только свои посты')
        instance.delete()

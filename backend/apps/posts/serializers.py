from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Post

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'handle']


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'excerpt', 'author', 'published', 'created_at', 'updated_at']

    def get_excerpt(self, obj):
        text = obj.content.strip().replace('\n', ' ')
        return text[:200] + ('…' if len(text) > 200 else '')


class PostDetailSerializer(PostListSerializer):
    content = serializers.CharField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['content']


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content', 'published']

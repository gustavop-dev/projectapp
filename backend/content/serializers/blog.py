from rest_framework import serializers

from content.models import BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing blog posts on public and admin views.
    """

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'cover_image',
            'excerpt', 'is_published', 'published_at', 'created_at',
        )


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a single blog post, including content and sources.
    """

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'cover_image',
            'excerpt', 'content', 'sources',
            'is_published', 'published_at',
            'created_at', 'updated_at',
        )


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating blog posts from the admin panel.
    """

    class Meta:
        model = BlogPost
        fields = (
            'title', 'slug', 'cover_image',
            'excerpt', 'content', 'sources',
            'is_published', 'published_at',
        )
        extra_kwargs = {
            'slug': {'required': False},
            'published_at': {'required': False},
        }

    def validate_sources(self, value):
        """Ensure sources is a list of objects with name and url."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                'sources must be a JSON array.'
            )
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    'Each source must be a JSON object.'
                )
            if 'name' not in item or 'url' not in item:
                raise serializers.ValidationError(
                    'Each source must have "name" and "url" keys.'
                )
        return value

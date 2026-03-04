from rest_framework import serializers

from content.models import BlogPost


def _get_lang(serializer):
    """Return 'es' or 'en' from serializer context (default 'es')."""
    request = serializer.context.get('request')
    if request:
        lang = request.query_params.get('lang', 'es')
        return lang if lang in ('es', 'en') else 'es'
    return serializer.context.get('lang', 'es')


# ---------------------------------------------------------------------------
# Public serializers — expose virtual title/excerpt/content based on lang
# ---------------------------------------------------------------------------

class BlogPostListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing blog posts on public and admin views.
    Exposes language-resolved title and excerpt fields.
    """
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'cover_image',
            'excerpt', 'is_published', 'published_at', 'created_at',
        )

    def get_title(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'title_{lang}')

    def get_excerpt(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'excerpt_{lang}')


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a single blog post, including content and sources.
    Exposes language-resolved title, excerpt and content fields.
    """
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'cover_image',
            'excerpt', 'content', 'sources',
            'is_published', 'published_at',
            'created_at', 'updated_at',
        )

    def get_title(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'title_{lang}')

    def get_excerpt(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'excerpt_{lang}')

    def get_content(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'content_{lang}')


# ---------------------------------------------------------------------------
# Admin serializers — expose all _es/_en fields
# ---------------------------------------------------------------------------

class BlogPostAdminListSerializer(serializers.ModelSerializer):
    """
    Admin list serializer — returns both language titles.
    """

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title_es', 'title_en', 'slug', 'cover_image',
            'excerpt_es', 'excerpt_en',
            'is_published', 'published_at', 'created_at',
        )


class BlogPostAdminDetailSerializer(serializers.ModelSerializer):
    """
    Admin detail serializer — returns all bilingual fields.
    """

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title_es', 'title_en', 'slug', 'cover_image',
            'excerpt_es', 'excerpt_en',
            'content_es', 'content_en',
            'sources', 'is_published', 'published_at',
            'created_at', 'updated_at',
        )


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating blog posts from the admin panel.
    """

    class Meta:
        model = BlogPost
        fields = (
            'title_es', 'title_en', 'slug', 'cover_image',
            'excerpt_es', 'excerpt_en',
            'content_es', 'content_en',
            'sources', 'is_published', 'published_at',
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

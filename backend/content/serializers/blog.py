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
            'excerpt', 'category', 'read_time_minutes', 'is_featured',
            'is_published', 'published_at', 'created_at',
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
    Exposes language-resolved title, excerpt, content and content_json fields.
    """
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    content_json = serializers.SerializerMethodField()
    meta_title = serializers.SerializerMethodField()
    meta_description = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            'id', 'title', 'slug', 'cover_image',
            'excerpt', 'content', 'content_json', 'sources',
            'category', 'read_time_minutes', 'is_featured',
            'meta_title', 'meta_description',
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

    def get_content_json(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'content_json_{lang}')

    def get_meta_title(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'meta_title_{lang}')

    def get_meta_description(self, obj):
        lang = _get_lang(self)
        return getattr(obj, f'meta_description_{lang}')


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
            'category', 'read_time_minutes', 'is_featured',
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
            'content_json_es', 'content_json_en',
            'sources', 'category', 'read_time_minutes', 'is_featured',
            'meta_title_es', 'meta_title_en',
            'meta_description_es', 'meta_description_en',
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
            'title_es', 'title_en', 'slug', 'cover_image',
            'excerpt_es', 'excerpt_en',
            'content_es', 'content_en',
            'content_json_es', 'content_json_en',
            'sources', 'category', 'read_time_minutes', 'is_featured',
            'meta_title_es', 'meta_title_en',
            'meta_description_es', 'meta_description_en',
            'is_published', 'published_at',
        )
        extra_kwargs = {
            'slug': {'required': False},
            'published_at': {'required': False},
            'content_es': {'required': False},
            'content_en': {'required': False},
            'content_json_es': {'required': False},
            'content_json_en': {'required': False},
            'category': {'required': False},
            'read_time_minutes': {'required': False},
            'is_featured': {'required': False},
            'meta_title_es': {'required': False},
            'meta_title_en': {'required': False},
            'meta_description_es': {'required': False},
            'meta_description_en': {'required': False},
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

    def validate_content_json_es(self, value):
        return _validate_content_json(value)

    def validate_content_json_en(self, value):
        return _validate_content_json(value)


# ---------------------------------------------------------------------------
# JSON content validation helper
# ---------------------------------------------------------------------------

ALLOWED_SECTION_KEYS = {'heading', 'content', 'list', 'subsections', 'timeline', 'examples'}


def _validate_content_json(value):
    """Validate the structured JSON content schema."""
    if not value:
        return value
    if not isinstance(value, dict):
        raise serializers.ValidationError('content_json must be a JSON object.')
    if 'intro' not in value or 'sections' not in value:
        raise serializers.ValidationError(
            'content_json must include "intro" and "sections" keys.'
        )
    if not isinstance(value['sections'], list):
        raise serializers.ValidationError('"sections" must be a list.')
    for i, section in enumerate(value['sections']):
        if not isinstance(section, dict):
            raise serializers.ValidationError(
                f'sections[{i}] must be a JSON object.'
            )
        if 'heading' not in section:
            raise serializers.ValidationError(
                f'sections[{i}] must have a "heading" key.'
            )
    return value


# ---------------------------------------------------------------------------
# JSON blog template
# ---------------------------------------------------------------------------

BLOG_JSON_TEMPLATE = {
    'intro': 'Introductory paragraph for the blog post.',
    'sections': [
        {
            'heading': 'Section Title',
            'content': 'Paragraph text for this section.',
            'list': ['Item one', 'Item two', 'Item three'],
        },
        {
            'heading': 'Another Section',
            'content': 'More content here.',
            'subsections': [
                {'title': 'Subsection A', 'description': 'Description of subsection A.'},
                {'title': 'Subsection B', 'description': 'Description of subsection B.'},
            ],
        },
        {
            'heading': 'Process / Timeline',
            'content': 'How the process works:',
            'timeline': [
                {'step': 'Step 1', 'description': 'First step description.'},
                {'step': 'Step 2', 'description': 'Second step description.'},
            ],
        },
        {
            'heading': 'Examples',
            'content': 'Real-world use cases:',
            'examples': ['Example one', 'Example two'],
        },
    ],
    'conclusion': 'Concluding paragraph summarising the article.',
    'cta': 'Call to action text inviting the reader to take the next step.',
}


class BlogPostFromJSONSerializer(serializers.Serializer):
    """
    Serializer for creating a blog post from a complete JSON payload.
    Mirrors the ProposalFromJSONSerializer pattern.
    """
    title_es = serializers.CharField(max_length=255)
    title_en = serializers.CharField(max_length=255)
    excerpt_es = serializers.CharField()
    excerpt_en = serializers.CharField()
    content_json_es = serializers.DictField(required=True)
    content_json_en = serializers.DictField(required=False, default=dict)
    cover_image = serializers.CharField(required=False, default='', allow_blank=True)
    sources = serializers.ListField(
        child=serializers.DictField(), required=False, default=list,
    )
    category = serializers.CharField(max_length=50, required=False, default='')
    read_time_minutes = serializers.IntegerField(required=False, default=0)
    is_featured = serializers.BooleanField(required=False, default=False)
    is_published = serializers.BooleanField(required=False, default=False)
    meta_title_es = serializers.CharField(max_length=255, required=False, default='', allow_blank=True)
    meta_title_en = serializers.CharField(max_length=255, required=False, default='', allow_blank=True)
    meta_description_es = serializers.CharField(required=False, default='', allow_blank=True)
    meta_description_en = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_content_json_es(self, value):
        return _validate_content_json(value)

    def validate_content_json_en(self, value):
        if not value:
            return value
        return _validate_content_json(value)

    def validate_sources(self, value):
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError('Each source must be a JSON object.')
            if 'name' not in item or 'url' not in item:
                raise serializers.ValidationError(
                    'Each source must have "name" and "url" keys.'
                )
        return value

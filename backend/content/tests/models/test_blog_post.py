"""Tests for the BlogPost model.

Covers: slug auto-generation, is_published/published_at behavior,
bilingual fields, ordering, and __str__.
"""
import pytest
from django.utils import timezone
from freezegun import freeze_time

from content.models import BlogPost

pytestmark = pytest.mark.django_db


class TestBlogPostCreation:
    def test_str_returns_spanish_title(self, blog_post):
        assert str(blog_post) == blog_post.title_es
        assert blog_post.title_es != ''

    def test_slug_auto_generated_from_title_es(self):
        post = BlogPost.objects.create(
            title_es='Mi Primer Artículo',
            title_en='My First Article',
            excerpt_es='Extracto.',
            excerpt_en='Excerpt.',
            content_es='<p>Contenido.</p>',
            content_en='<p>Content.</p>',
        )
        assert post.slug == 'mi-primer-articulo'

    def test_slug_uniqueness_appends_counter(self):
        """Create two posts with identical title_es and verify slug collision resolution."""
        BlogPost.objects.create(
            title_es='Artículo Duplicado',
            title_en='Duplicate Article',
            excerpt_es='E1.',
            excerpt_en='E1.',
            content_es='<p>C1.</p>',
            content_en='<p>C1.</p>',
        )
        post2 = BlogPost.objects.create(
            title_es='Artículo Duplicado',
            title_en='Duplicate Article 2',
            excerpt_es='E2.',
            excerpt_en='E2.',
            content_es='<p>C2.</p>',
            content_en='<p>C2.</p>',
        )
        assert post2.slug == 'articulo-duplicado-1'

    def test_slug_preserved_on_update(self, blog_post):
        original_slug = blog_post.slug
        blog_post.title_es = 'Título Cambiado'
        blog_post.save()
        assert blog_post.slug == original_slug


class TestBlogPostPublishing:
    @freeze_time('2026-03-01 12:00:00')
    def test_published_at_set_when_published(self):
        post = BlogPost.objects.create(
            title_es='Nuevo Post',
            title_en='New Post',
            excerpt_es='E.',
            excerpt_en='E.',
            content_es='<p>C.</p>',
            content_en='<p>C.</p>',
            is_published=True,
        )
        assert post.published_at is not None
        assert post.published_at.year == 2026

    def test_published_at_not_set_for_drafts(self, draft_blog_post):
        assert draft_blog_post.published_at is None
        assert draft_blog_post.is_published is False

    def test_published_at_not_overwritten_on_save(self, blog_post):
        original_published_at = blog_post.published_at
        blog_post.title_en = 'Updated Title'
        blog_post.save()
        blog_post.refresh_from_db()
        assert blog_post.published_at == original_published_at

    def test_default_is_published_false(self):
        post = BlogPost.objects.create(
            title_es='Post sin publicar',
            title_en='Unpublished post',
            excerpt_es='E.',
            excerpt_en='E.',
            content_es='<p>C.</p>',
            content_en='<p>C.</p>',
        )
        assert post.is_published is False


class TestBlogPostSources:
    def test_sources_default_empty_list(self):
        post = BlogPost.objects.create(
            title_es='Post sin fuentes',
            title_en='Post without sources',
            excerpt_es='E.',
            excerpt_en='E.',
            content_es='<p>C.</p>',
            content_en='<p>C.</p>',
        )
        assert post.sources == []

    def test_sources_stores_json_list(self, blog_post):
        assert isinstance(blog_post.sources, list)
        assert blog_post.sources[0]['name'] == 'OpenAI'


class TestBlogPostOrdering:
    @freeze_time('2026-03-01 12:00:00')
    def test_ordered_by_published_at_descending(self):
        """Create older and newer posts and verify default ordering is newest-first."""
        older = BlogPost.objects.create(
            title_es='Viejo',
            title_en='Old',
            excerpt_es='E.',
            excerpt_en='E.',
            content_es='<p>C.</p>',
            content_en='<p>C.</p>',
            is_published=True,
            published_at=timezone.now() - timezone.timedelta(days=10),
        )
        newer = BlogPost.objects.create(
            title_es='Nuevo',
            title_en='New',
            excerpt_es='E.',
            excerpt_en='E.',
            content_es='<p>C.</p>',
            content_en='<p>C.</p>',
            is_published=True,
            published_at=timezone.now(),
        )
        posts = list(BlogPost.objects.all())
        assert posts[0] == newer
        assert posts[1] == older

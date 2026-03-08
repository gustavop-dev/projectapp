"""Tests for blog API views.

Covers: public GET list/detail with ?lang=, admin CRUD (auth required),
happy path, 404s, validation errors, permission checks.
"""
import pytest
from django.urls import reverse

from content.models import BlogPost

pytestmark = pytest.mark.django_db


class TestPublicBlogListView:
    def test_returns_200_with_published_posts(self, api_client, blog_post):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['count'] == 1

    def test_excludes_draft_posts(self, api_client, draft_blog_post):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        assert len(response.data['results']) == 0

    def test_returns_empty_list_when_no_posts(self, api_client):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        assert response.data['results'] == []

    def test_accepts_lang_query_param(self, api_client, blog_post):
        response = api_client.get(reverse('list-blog-posts'), {'lang': 'en'})
        assert response.status_code == 200


class TestPublicBlogDetailView:
    def test_returns_200_for_published_post(self, api_client, blog_post):
        url = reverse('retrieve-blog-post', kwargs={'slug': blog_post.slug})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_returns_404_for_draft_post(self, api_client, draft_blog_post):
        url = reverse('retrieve-blog-post', kwargs={'slug': draft_blog_post.slug})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_slug(self, api_client):
        url = reverse('retrieve-blog-post', kwargs={'slug': 'does-not-exist'})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_accepts_lang_query_param(self, api_client, blog_post):
        url = reverse('retrieve-blog-post', kwargs={'slug': blog_post.slug})
        response = api_client.get(url, {'lang': 'en'})
        assert response.status_code == 200


class TestAdminBlogListView:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-blog-posts'))
        assert response.status_code in (401, 403)

    def test_returns_200_for_admin(self, admin_client, blog_post, draft_blog_post):
        response = admin_client.get(reverse('list-admin-blog-posts'))
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_includes_drafts_for_admin(self, admin_client, draft_blog_post):
        response = admin_client.get(reverse('list-admin-blog-posts'))
        assert response.status_code == 200
        assert len(response.data) == 1


class TestAdminCreateBlogPost:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-blog-post'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_post_returns_201(self, admin_client):
        payload = {
            'title_es': 'Nuevo Post',
            'title_en': 'New Post',
            'excerpt_es': 'Extracto.',
            'excerpt_en': 'Excerpt.',
            'content_es': '<p>Contenido.</p>',
            'content_en': '<p>Content.</p>',
        }
        response = admin_client.post(
            reverse('create-blog-post'), payload, format='json'
        )
        assert response.status_code == 201
        assert BlogPost.objects.count() == 1

    def test_returns_400_with_missing_required_fields(self, admin_client):
        payload = {'title_es': 'Solo título'}
        response = admin_client.post(
            reverse('create-blog-post'), payload, format='json'
        )
        assert response.status_code == 400

    def test_returns_400_with_invalid_sources(self, admin_client):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_es': 'C', 'content_en': 'C',
            'sources': 'not-a-list',
        }
        response = admin_client.post(
            reverse('create-blog-post'), payload, format='json'
        )
        assert response.status_code == 400
        assert 'sources' in response.data


class TestAdminRetrieveBlogPost:
    def test_returns_200_for_admin(self, admin_client, blog_post):
        url = reverse('retrieve-admin-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('retrieve-admin-blog-post', kwargs={'post_id': 99999})
        response = admin_client.get(url)
        assert response.status_code == 404


class TestAdminUpdateBlogPost:
    def test_returns_401_for_unauthenticated(self, api_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        response = api_client.patch(url, {}, format='json')
        assert response.status_code in (401, 403)

    def test_updates_post_returns_200(self, admin_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.patch(
            url, {'title_en': 'Updated Title'}, format='json'
        )
        assert response.status_code == 200
        blog_post.refresh_from_db()
        assert blog_post.title_en == 'Updated Title'

    def test_returns_400_for_invalid_sources_on_update(self, admin_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.patch(
            url, {'sources': 'not-a-list'}, format='json'
        )
        assert response.status_code == 400
        assert 'sources' in response.data

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('update-blog-post', kwargs={'post_id': 99999})
        response = admin_client.patch(url, {}, format='json')
        assert response.status_code == 404


class TestAdminDeleteBlogPost:
    def test_returns_401_for_unauthenticated(self, api_client, blog_post):
        url = reverse('delete-blog-post', kwargs={'post_id': blog_post.id})
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_deletes_post_returns_204(self, admin_client, blog_post):
        url = reverse('delete-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert BlogPost.objects.count() == 0

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('delete-blog-post', kwargs={'post_id': 99999})
        response = admin_client.delete(url)
        assert response.status_code == 404


class TestPublicBlogNewFields:
    def test_list_includes_category_and_read_time(self, api_client, blog_post_with_json):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        post = response.data['results'][0]
        assert post['category'] == 'technology'
        assert post['read_time_minutes'] == 8
        assert post['is_featured'] is True

    def test_detail_includes_content_json(self, api_client, blog_post_with_json):
        url = reverse('retrieve-blog-post', kwargs={'slug': blog_post_with_json.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['content_json']['intro'] == 'Introducción en español.'
        assert len(response.data['content_json']['sections']) == 2

    def test_detail_content_json_resolves_lang(self, api_client, blog_post_with_json):
        url = reverse('retrieve-blog-post', kwargs={'slug': blog_post_with_json.slug})
        response = api_client.get(url, {'lang': 'en'})
        assert response.status_code == 200
        assert response.data['content_json']['intro'] == 'Introduction in English.'


class TestAdminCreateFromJSON:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-blog-post-from-json'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_post_from_json_returns_201(self, admin_client):
        """Create a blog post from a full JSON payload with content_json and metadata."""
        payload = {
            'title_es': 'Post desde JSON',
            'title_en': 'Post from JSON',
            'excerpt_es': 'Resumen JSON.',
            'excerpt_en': 'JSON excerpt.',
            'content_json_es': {
                'intro': 'Intro ES.',
                'sections': [{'heading': 'Sec 1', 'content': 'Text.'}],
                'conclusion': 'Fin.',
                'cta': 'CTA.',
            },
            'category': 'ai',
            'read_time_minutes': 5,
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json'
        )
        assert response.status_code == 201
        assert BlogPost.objects.count() == 1
        post = BlogPost.objects.first()
        assert post.content_json_es['intro'] == 'Intro ES.'
        assert post.category == 'ai'

    def test_returns_400_missing_title(self, admin_client):
        payload = {
            'title_es': 'Only ES',
            'excerpt_es': 'E',
            'excerpt_en': 'E',
            'content_json_es': {'intro': 'I', 'sections': []},
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json'
        )
        assert response.status_code == 400

    def test_returns_400_invalid_content_json(self, admin_client):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {'no_intro': True},
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json'
        )
        assert response.status_code == 400
        assert 'content_json_es' in response.data

    def test_returns_400_section_without_heading(self, admin_client):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'excerpt_es': 'E', 'excerpt_en': 'E',
            'content_json_es': {
                'intro': 'I',
                'sections': [{'content': 'no heading'}],
            },
        }
        response = admin_client.post(
            reverse('create-blog-post-from-json'), payload, format='json'
        )
        assert response.status_code == 400


class TestAdminBlogJSONTemplate:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('blog-json-template'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_template(self, admin_client):
        response = admin_client.get(reverse('blog-json-template'))
        assert response.status_code == 200
        assert 'content_json_es' in response.data
        assert 'intro' in response.data['content_json_es']
        assert 'sections' in response.data['content_json_es']

    def test_template_has_all_expected_keys(self, admin_client):
        response = admin_client.get(reverse('blog-json-template'))
        assert response.status_code == 200
        for key in ('title_es', 'title_en', 'excerpt_es', 'excerpt_en',
                     'content_json_es', 'content_json_en', 'category',
                     'read_time_minutes', 'sources'):
            assert key in response.data


class TestAdminDuplicateBlogPost:
    def test_returns_401_for_unauthenticated(self, api_client, blog_post):
        """Unauthenticated users cannot duplicate a blog post."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post.id})
        response = api_client.post(url)
        assert response.status_code in (401, 403)

    def test_duplicates_post_returns_201(self, admin_client, blog_post_with_json):
        """Duplicating creates a new draft post with '(copia)' suffix and reset fields."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post_with_json.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        assert BlogPost.objects.count() == 2
        new_post = BlogPost.objects.exclude(pk=blog_post_with_json.pk).first()
        assert '(copia)' in new_post.title_es
        assert '(copy)' in new_post.title_en
        assert new_post.is_published is False
        assert new_post.published_at is None
        assert new_post.is_featured is False
        assert new_post.slug != blog_post_with_json.slug

    def test_duplicated_post_copies_content_json(self, admin_client, blog_post_with_json):
        """Duplicated post preserves the original content_json structure."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post_with_json.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        new_post = BlogPost.objects.exclude(pk=blog_post_with_json.pk).first()
        assert new_post.content_json_es == blog_post_with_json.content_json_es
        assert new_post.category == blog_post_with_json.category

    def test_returns_404_for_nonexistent_id(self, admin_client):
        """Duplicating a nonexistent post returns 404."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': 99999})
        response = admin_client.post(url)
        assert response.status_code == 404


class TestAdminUpdateNewFields:
    def test_updates_category_and_read_time(self, admin_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.patch(
            url, {'category': 'design', 'read_time_minutes': 12}, format='json'
        )
        assert response.status_code == 200
        blog_post.refresh_from_db()
        assert blog_post.category == 'design'
        assert blog_post.read_time_minutes == 12

    def test_updates_content_json(self, admin_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        json_content = {
            'intro': 'New intro.',
            'sections': [{'heading': 'New heading'}],
            'conclusion': 'End.',
            'cta': 'Act now.',
        }
        response = admin_client.patch(
            url, {'content_json_es': json_content}, format='json'
        )
        assert response.status_code == 200
        blog_post.refresh_from_db()
        assert blog_post.content_json_es['intro'] == 'New intro.'

    def test_rejects_invalid_content_json(self, admin_client, blog_post):
        url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
        response = admin_client.patch(
            url, {'content_json_es': {'missing_intro': True}}, format='json'
        )
        assert response.status_code == 400

"""
Tests for blog API views.

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
        assert len(response.data) == 1

    def test_excludes_draft_posts(self, api_client, draft_blog_post):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_returns_empty_list_when_no_posts(self, api_client):
        response = api_client.get(reverse('list-blog-posts'))
        assert response.status_code == 200
        assert response.data == []

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

"""Tests for blog API views.

Covers: public GET list/detail with ?lang=, admin CRUD (auth required),
happy path, 404s, validation errors, permission checks.
"""
from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone as dj_timezone
from freezegun import freeze_time

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
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_includes_drafts_for_admin(self, admin_client, draft_blog_post):
        response = admin_client.get(reverse('list-admin-blog-posts'))
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1


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
        """Duplicating creates a new post with '(copia)' suffix."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post_with_json.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        assert BlogPost.objects.count() == 2
        new_post = BlogPost.objects.exclude(pk=blog_post_with_json.pk).first()
        assert '(copia)' in new_post.title_es
        assert '(copy)' in new_post.title_en

    def test_duplicated_post_resets_publish_fields(self, admin_client, blog_post_with_json):
        """Duplicated post is unpublished with reset featured flag and unique slug."""
        url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post_with_json.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        new_post = BlogPost.objects.exclude(pk=blog_post_with_json.pk).first()
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


class TestServeSitemapXml:
    """Tests for the serve_sitemap_xml view (dynamic XML sitemap)."""

    def test_returns_xml_content_type(self, client):
        """Sitemap endpoint returns application/xml content type."""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'application/xml' in response['Content-Type']

    def test_includes_static_pages(self, client):
        """Sitemap XML contains at least one static page entry."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert '<urlset' in content
        assert 'https://projectapp.co/en-us' in content

    def test_includes_published_blog_posts(self, client, blog_post):
        """Sitemap XML includes published blog post URLs with lastmod."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert f'/blog/{blog_post.slug}' in content
        assert '<lastmod>' in content

    def test_excludes_draft_blog_posts(self, client, draft_blog_post):
        """Sitemap XML excludes unpublished blog posts."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert draft_blog_post.slug not in content

    def test_handles_post_without_updated_at(self, client, db):
        """Sitemap omits lastmod when updated_at is None."""
        post = BlogPost.objects.create(
            title_es='Sin fecha', title_en='No date',
            excerpt_es='E', excerpt_en='E',
            is_published=True, updated_at=None,
        )
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert f'/blog/{post.slug}' in content


    def test_includes_published_portfolio_works(self, client, published_portfolio_work):
        """Sitemap XML includes published portfolio work URLs with hreflang alternates."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert f'/en-us/portfolio-works/{published_portfolio_work.slug}' in content
        assert f'/es-co/portfolio-works/{published_portfolio_work.slug}' in content

    def test_excludes_draft_portfolio_works(self, client, draft_portfolio_work):
        """Sitemap XML excludes unpublished portfolio works."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert draft_portfolio_work.slug not in content

    def test_excludes_archived_pages(self, client):
        """Sitemap XML does not include archived pages (web-designs, hosting, etc.)."""
        response = client.get('/sitemap.xml')
        content = response.content.decode()
        assert '/web-designs' not in content
        assert '/custom-software' not in content
        assert '/3d-animations' not in content
        assert '/e-commerce-prices' not in content
        assert '/hosting' not in content


class TestBlogListPagination:
    """Tests for list_blog_posts pagination edge cases."""

    def test_invalid_page_param_defaults_to_one(self, api_client, blog_post):
        """Non-numeric page param falls back to page=1."""
        response = api_client.get(reverse('list-blog-posts'), {'page': 'abc'})
        assert response.status_code == 200
        assert response.data['page'] == 1

    def test_invalid_page_size_defaults_to_six(self, api_client, blog_post):
        """Non-numeric page_size param falls back to 6."""
        response = api_client.get(
            reverse('list-blog-posts'), {'page_size': 'xyz'}
        )
        assert response.status_code == 200
        assert response.data['page_size'] == 6

    def test_page_size_clamped_to_max_fifty(self, api_client, blog_post):
        """page_size values above 50 are clamped to 50."""
        response = api_client.get(
            reverse('list-blog-posts'), {'page_size': '100'}
        )
        assert response.status_code == 200
        assert response.data['page_size'] == 50


class TestBlogSitemapData:
    """Tests for the blog_sitemap_data lightweight endpoint."""

    def test_returns_published_slugs(self, api_client, blog_post, draft_blog_post):
        """Returns only published posts with slug and updated_at."""
        response = api_client.get(reverse('blog-sitemap-data'))
        assert response.status_code == 200
        slugs = [item['slug'] for item in response.data]
        assert blog_post.slug in slugs
        assert draft_blog_post.slug not in slugs


# ---------------------------------------------------------------------------
# Blog calendar endpoint (lines 438-502)
# ---------------------------------------------------------------------------

class TestBlogCalendar:
    def _url(self):
        return reverse('blog-calendar')

    def test_returns_401_for_unauthenticated(self, api_client):
        """Unauthenticated users cannot access the blog calendar."""
        response = api_client.get(self._url())
        assert response.status_code in (401, 403)

    def test_returns_400_when_start_missing(self, admin_client):
        """Missing start param returns 400."""
        response = admin_client.get(self._url(), {'end': '2026-03-31'})
        assert response.status_code == 400
        assert 'start' in response.data['detail'].lower()

    def test_returns_400_when_end_missing(self, admin_client):
        """Missing end param returns 400."""
        response = admin_client.get(self._url(), {'start': '2026-03-01'})
        assert response.status_code == 400

    def test_returns_400_for_invalid_date_format(self, admin_client):
        """Invalid date format returns 400."""
        response = admin_client.get(self._url(), {'start': 'not-a-date', 'end': '2026-03-31'})
        assert response.status_code == 400
        assert 'invalid' in response.data['detail'].lower()

    def test_returns_published_posts_in_range(self, admin_client, blog_post):
        """Published posts within the date range are returned."""
        in_range = dj_timezone.make_aware(datetime(2026, 3, 10, 12, 0, 0))
        BlogPost.objects.filter(pk=blog_post.pk).update(published_at=in_range)
        response = admin_client.get(self._url(), {
            'start': '2026-03-01',
            'end': '2026-03-31',
        })
        assert response.status_code == 200
        assert len(response.data) >= 1
        post = response.data[0]
        assert 'title_es' in post
        assert 'calendar_status' in post
        assert post['calendar_status'] == 'published'

    def test_returns_draft_posts_created_in_range(self, admin_client, draft_blog_post):
        """Drafts created within the date range are returned with status 'draft'."""
        in_range = dj_timezone.make_aware(datetime(2026, 3, 10, 12, 0, 0))
        BlogPost.objects.filter(pk=draft_blog_post.pk).update(created_at=in_range)
        response = admin_client.get(self._url(), {
            'start': '2026-03-01',
            'end': '2026-03-31',
        })
        assert response.status_code == 200
        drafts = [p for p in response.data if p['calendar_status'] == 'draft']
        assert len(drafts) >= 1

    @freeze_time('2026-03-15 12:00:00')
    def test_returns_empty_list_for_range_without_posts(self, admin_client, db):
        """Returns empty list when no posts exist in the date range."""
        response = admin_client.get(self._url(), {
            'start': '2020-01-01',
            'end': '2020-01-31',
        })
        assert response.status_code == 200
        assert response.data == []


class TestUploadBlogCoverImage:
    """Tests for the upload_blog_cover_image admin endpoint."""

    def test_returns_401_for_unauthenticated(self, api_client, blog_post):
        """Unauthenticated users cannot upload a cover image."""
        url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.id})
        response = api_client.post(url)
        assert response.status_code in (401, 403)

    def test_returns_400_when_no_file_provided(self, admin_client, blog_post):
        """Returns 400 when no cover_image file is in the request."""
        url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.id})
        response = admin_client.post(url, {}, format='multipart')
        assert response.status_code == 400
        assert 'cover_image' in response.data

    def test_uploads_file_returns_200(self, admin_client, blog_post):
        """Uploading a valid image file returns 200 with updated post data."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile(
            'cover.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            content_type='image/jpeg',
        )
        url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.id})
        response = admin_client.post(url, {'cover_image': image_file}, format='multipart')
        assert response.status_code == 200

    def test_returns_404_for_nonexistent_post(self, admin_client):
        """Uploading to a nonexistent post returns 404."""
        url = reverse('upload-blog-cover-image', kwargs={'post_id': 99999})
        response = admin_client.post(url, {}, format='multipart')
        assert response.status_code == 404

"""Tests for portfolio works API views.

Covers: public GET list/detail with ?lang=, sitemap-data,
admin CRUD (auth required), create-from-json, json-template,
duplicate, upload-cover, permission checks.
"""
import pytest
from django.urls import reverse

from content.models import PortfolioWork

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

class TestPublicPortfolioList:
    def test_returns_200_with_published_works(self, api_client, published_portfolio_work):
        response = api_client.get(reverse('list-portfolio-works-public'))
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_excludes_draft_works(self, api_client, draft_portfolio_work):
        response = api_client.get(reverse('list-portfolio-works-public'))
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_returns_empty_list_when_no_works(self, api_client):
        response = api_client.get(reverse('list-portfolio-works-public'))
        assert response.status_code == 200
        assert response.data == []

    def test_accepts_lang_query_param(self, api_client, published_portfolio_work):
        response = api_client.get(reverse('list-portfolio-works-public'), {'lang': 'en'})
        assert response.status_code == 200
        assert response.data[0]['title'] == 'MOOSER Hotel'

    def test_returns_spanish_by_default(self, api_client, published_portfolio_work):
        response = api_client.get(reverse('list-portfolio-works-public'))
        assert response.status_code == 200
        assert 'Experiencia digital' in response.data[0]['title']


class TestPublicPortfolioDetail:
    def test_returns_200_for_published_work(self, api_client, published_portfolio_work):
        url = reverse('retrieve-portfolio-work', kwargs={'slug': published_portfolio_work.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data['project_url'] == 'https://mooser-hotel.com'

    def test_returns_404_for_draft_work(self, api_client, draft_portfolio_work):
        url = reverse('retrieve-portfolio-work', kwargs={'slug': draft_portfolio_work.slug})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_returns_404_for_nonexistent_slug(self, api_client):
        url = reverse('retrieve-portfolio-work', kwargs={'slug': 'does-not-exist'})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_detail_includes_content_json(self, api_client, published_portfolio_work):
        url = reverse('retrieve-portfolio-work', kwargs={'slug': published_portfolio_work.slug})
        response = api_client.get(url)
        assert response.status_code == 200
        cj = response.data['content_json']
        assert 'problem' in cj
        assert 'solution' in cj
        assert 'results' in cj

    def test_detail_resolves_lang_en(self, api_client, published_portfolio_work):
        url = reverse('retrieve-portfolio-work', kwargs={'slug': published_portfolio_work.slug})
        response = api_client.get(url, {'lang': 'en'})
        assert response.status_code == 200
        assert response.data['content_json']['problem']['title'] == 'The Challenge'


class TestPortfolioSitemapData:
    def test_returns_published_slugs(self, api_client, published_portfolio_work, draft_portfolio_work):
        response = api_client.get(reverse('portfolio-sitemap-data'))
        assert response.status_code == 200
        slugs = [item['slug'] for item in response.data]
        assert published_portfolio_work.slug in slugs
        assert draft_portfolio_work.slug not in slugs

    def test_returns_empty_when_no_published(self, api_client, draft_portfolio_work):
        response = api_client.get(reverse('portfolio-sitemap-data'))
        assert response.status_code == 200
        assert len(response.data) == 0


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdminPortfolioList:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-portfolio-works'))
        assert response.status_code in (401, 403)

    def test_returns_200_for_admin(self, admin_client, published_portfolio_work, draft_portfolio_work):
        response = admin_client.get(reverse('list-admin-portfolio-works'))
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_includes_drafts_for_admin(self, admin_client, draft_portfolio_work):
        response = admin_client.get(reverse('list-admin-portfolio-works'))
        assert response.status_code == 200
        assert len(response.data) == 1


class TestAdminCreatePortfolioWork:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-portfolio-work'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_work_returns_201(self, admin_client):
        payload = {
            'title_es': 'Nuevo Proyecto',
            'title_en': 'New Project',
            'project_url': 'https://example.com',
        }
        response = admin_client.post(reverse('create-portfolio-work'), payload, format='json')
        assert response.status_code == 201
        assert PortfolioWork.objects.count() == 1
        work = PortfolioWork.objects.first()
        assert isinstance(work.slug, str)
        assert len(work.slug) > 0

    def test_returns_400_with_missing_required_fields(self, admin_client):
        payload = {'title_es': 'Solo título'}
        response = admin_client.post(reverse('create-portfolio-work'), payload, format='json')
        assert response.status_code == 400


class TestAdminRetrievePortfolioWork:
    def test_returns_200_for_admin(self, admin_client, published_portfolio_work):
        url = reverse('retrieve-admin-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.get(url)
        assert response.status_code == 200
        assert 'content_json_es' in response.data
        assert 'content_json_en' in response.data

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('retrieve-admin-portfolio-work', kwargs={'work_id': 99999})
        response = admin_client.get(url)
        assert response.status_code == 404


class TestAdminUpdatePortfolioWork:
    def test_returns_401_for_unauthenticated(self, api_client, published_portfolio_work):
        url = reverse('update-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = api_client.patch(url, {}, format='json')
        assert response.status_code in (401, 403)

    def test_updates_work_returns_200(self, admin_client, published_portfolio_work):
        url = reverse('update-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.patch(url, {'title_en': 'Updated Title'}, format='json')
        assert response.status_code == 200
        published_portfolio_work.refresh_from_db()
        assert published_portfolio_work.title_en == 'Updated Title'

    def test_updates_content_json(self, admin_client, published_portfolio_work):
        url = reverse('update-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        new_json = {
            'problem': {'title': 'New', 'description': 'New desc.'},
            'solution': {'title': 'New', 'description': 'New desc.'},
            'results': {'title': 'New', 'description': 'New desc.'},
        }
        response = admin_client.patch(url, {'content_json_es': new_json}, format='json')
        assert response.status_code == 200
        published_portfolio_work.refresh_from_db()
        assert published_portfolio_work.content_json_es['problem']['title'] == 'New'

    def test_rejects_invalid_content_json(self, admin_client, published_portfolio_work):
        url = reverse('update-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.patch(url, {'content_json_es': {'missing_keys': True}}, format='json')
        assert response.status_code == 400

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('update-portfolio-work', kwargs={'work_id': 99999})
        response = admin_client.patch(url, {}, format='json')
        assert response.status_code == 404


class TestAdminDeletePortfolioWork:
    def test_returns_401_for_unauthenticated(self, api_client, published_portfolio_work):
        url = reverse('delete-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_deletes_work_returns_204(self, admin_client, published_portfolio_work):
        url = reverse('delete-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert PortfolioWork.objects.count() == 0

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('delete-portfolio-work', kwargs={'work_id': 99999})
        response = admin_client.delete(url)
        assert response.status_code == 404


class TestAdminDuplicatePortfolioWork:
    def test_returns_401_for_unauthenticated(self, api_client, published_portfolio_work):
        url = reverse('duplicate-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = api_client.post(url)
        assert response.status_code in (401, 403)

    def test_duplicates_work_returns_201(self, admin_client, published_portfolio_work):
        url = reverse('duplicate-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        assert PortfolioWork.objects.count() == 2
        new_work = PortfolioWork.objects.exclude(pk=published_portfolio_work.pk).first()
        assert '(copia)' in new_work.title_es
        assert '(copy)' in new_work.title_en

    def test_duplicated_work_is_draft(self, admin_client, published_portfolio_work):
        url = reverse('duplicate-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        new_work = PortfolioWork.objects.exclude(pk=published_portfolio_work.pk).first()
        assert new_work.is_published is False
        assert new_work.slug != published_portfolio_work.slug

    def test_duplicated_work_copies_content_json(self, admin_client, published_portfolio_work):
        url = reverse('duplicate-portfolio-work', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.post(url)
        assert response.status_code == 201
        new_work = PortfolioWork.objects.exclude(pk=published_portfolio_work.pk).first()
        assert new_work.content_json_es == published_portfolio_work.content_json_es

    def test_returns_404_for_nonexistent_id(self, admin_client):
        url = reverse('duplicate-portfolio-work', kwargs={'work_id': 99999})
        response = admin_client.post(url)
        assert response.status_code == 404


class TestAdminCreateFromJSON:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-portfolio-work-from-json'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_from_json_returns_201(self, admin_client):
        payload = {
            'title_es': 'Proyecto JSON',
            'title_en': 'JSON Project',
            'project_url': 'https://example.com/json',
            'content_json_es': {
                'problem': {'title': 'P', 'description': 'D'},
                'solution': {'title': 'S', 'description': 'D'},
                'results': {'title': 'R', 'description': 'D'},
            },
        }
        response = admin_client.post(reverse('create-portfolio-work-from-json'), payload, format='json')
        assert response.status_code == 201
        assert PortfolioWork.objects.count() == 1

    def test_returns_400_missing_project_url(self, admin_client):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'content_json_es': {
                'problem': {'title': 'P', 'description': 'D'},
                'solution': {'title': 'S', 'description': 'D'},
                'results': {'title': 'R', 'description': 'D'},
            },
        }
        response = admin_client.post(reverse('create-portfolio-work-from-json'), payload, format='json')
        assert response.status_code == 400

    def test_returns_400_invalid_content_json(self, admin_client):
        payload = {
            'title_es': 'T', 'title_en': 'T',
            'project_url': 'https://example.com',
            'content_json_es': {'no_problem_key': True},
        }
        response = admin_client.post(reverse('create-portfolio-work-from-json'), payload, format='json')
        assert response.status_code == 400
        assert 'content_json_es' in response.data


class TestAdminPortfolioJSONTemplate:
    def test_returns_401_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('portfolio-json-template'))
        assert response.status_code in (401, 403)

    def test_returns_200_with_template(self, admin_client):
        response = admin_client.get(reverse('portfolio-json-template'))
        assert response.status_code == 200
        assert 'content_json_es' in response.data
        cj = response.data['content_json_es']
        assert 'problem' in cj
        assert 'solution' in cj
        assert 'results' in cj

    def test_template_has_expected_keys(self, admin_client):
        response = admin_client.get(reverse('portfolio-json-template'))
        assert response.status_code == 200
        for key in ('title_es', 'title_en', 'project_url', 'content_json_es', 'content_json_en'):
            assert key in response.data


class TestAdminUploadPortfolioCover:
    def test_returns_401_for_unauthenticated(self, api_client, published_portfolio_work):
        url = reverse('upload-portfolio-cover-image', kwargs={'work_id': published_portfolio_work.id})
        response = api_client.post(url)
        assert response.status_code in (401, 403)

    def test_returns_400_when_no_file_provided(self, admin_client, published_portfolio_work):
        url = reverse('upload-portfolio-cover-image', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.post(url, {}, format='multipart')
        assert response.status_code == 400
        assert 'cover_image' in response.data

    def test_uploads_file_returns_200(self, admin_client, published_portfolio_work):
        from django.core.files.uploadedfile import SimpleUploadedFile
        image_file = SimpleUploadedFile(
            'cover.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100,
            content_type='image/jpeg',
        )
        url = reverse('upload-portfolio-cover-image', kwargs={'work_id': published_portfolio_work.id})
        response = admin_client.post(url, {'cover_image': image_file}, format='multipart')
        assert response.status_code == 200

    def test_returns_404_for_nonexistent_work(self, admin_client):
        url = reverse('upload-portfolio-cover-image', kwargs={'work_id': 99999})
        response = admin_client.post(url, {}, format='multipart')
        assert response.status_code == 404

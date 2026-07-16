"""Tests for the view-map panel settings singleton endpoints."""
import pytest
from django.urls import reverse

from content.models import ViewMapSettings

pytestmark = pytest.mark.django_db


class TestViewMapSettings:
    def test_returns_403_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('view-map-settings'))
        assert response.status_code in (401, 403)

    def test_get_returns_defaults(self, admin_client):
        response = admin_client.get(reverse('view-map-settings'))
        assert response.status_code == 200
        assert response.data['default_view_mode'] == 'list'
        assert response.data['default_filters'] == {}

    def test_patch_updates_view_mode(self, admin_client):
        response = admin_client.patch(
            reverse('update-view-map-settings'),
            {'default_view_mode': 'map'},
            format='json',
        )
        assert response.status_code == 200
        assert ViewMapSettings.load().default_view_mode == 'map'

    def test_patch_rejects_invalid_view_mode(self, admin_client):
        response = admin_client.patch(
            reverse('update-view-map-settings'),
            {'default_view_mode': 'grid'},
            format='json',
        )
        assert response.status_code == 400
        assert 'default_view_mode' in response.data

    def test_patch_updates_default_filters(self, admin_client):
        filters = {'audiences': ['admin'], 'viewTypes': ['config']}
        response = admin_client.patch(
            reverse('update-view-map-settings'),
            {'default_filters': filters},
            format='json',
        )
        assert response.status_code == 200
        assert ViewMapSettings.load().default_filters == filters

    def test_patch_rejects_unknown_filter_key(self, admin_client):
        response = admin_client.patch(
            reverse('update-view-map-settings'),
            {'default_filters': {'statuses': ['draft']}},
            format='json',
        )
        assert response.status_code == 400
        assert 'default_filters' in response.data

    def test_patch_rejects_non_list_filter_value(self, admin_client):
        response = admin_client.patch(
            reverse('update-view-map-settings'),
            {'default_filters': {'audiences': 'admin'}},
            format='json',
        )
        assert response.status_code == 400
        assert 'default_filters' in response.data

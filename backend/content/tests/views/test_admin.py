"""Tests for Django admin configuration.

Covers: ProjectAppAdminSite.get_app_list() custom grouping,
model registrations.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from content.admin import admin_site

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestProjectAppAdminSiteGetAppList:
    def _make_superuser_request(self, db):
        user = User.objects.create_superuser(
            username='super_admin', email='super@test.com', password='pass123',
        )
        request = RequestFactory().get('/admin/')
        request.user = user
        return request

    def test_returns_8_custom_groups(self, db):
        request = self._make_superuser_request(db)
        app_list = admin_site.get_app_list(request)
        assert len(app_list) == 8

    def test_group_names_match_expected_labels(self, db):
        request = self._make_superuser_request(db)
        app_list = admin_site.get_app_list(request)
        names = {app['name'] for app in app_list}
        expected = {
            'Contact Management', 'Design Management',
            'Model3D Management', 'Portfolio Works Management',
            'Product Management', 'Hosting Management',
            'Business Proposals', 'Blog',
        }
        assert names == expected

    def test_product_management_group_includes_product_category_item(self, db):
        request = self._make_superuser_request(db)
        app_list = admin_site.get_app_list(request)
        product_group = next(a for a in app_list if a['name'] == 'Product Management')
        object_names = {m['object_name'] for m in product_group['models']}
        assert {'Product', 'Category', 'Item'}.issubset(object_names)

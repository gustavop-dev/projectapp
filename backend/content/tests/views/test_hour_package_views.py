"""Tests for the hour-package catalog admin CRUD endpoints."""
import pytest
from django.urls import reverse

from content.models import HourPackage, HourPackageSettings

pytestmark = pytest.mark.django_db


@pytest.fixture
def mex_package(db):
    return HourPackage.objects.create(
        nationality='MEX',
        name_es='Paquete Ágil MX',
        name_en='Agile Pack MX',
        hours=20,
        hourly_rate=45,
        discount_percent=0,
        order=1,
    )


class TestAdminHourPackageList:
    def test_returns_403_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('list-admin-hour-packages'))
        assert response.status_code in (401, 403)

    def test_lists_migration_seeded_col_packages(self, admin_client):
        response = admin_client.get(reverse('list-admin-hour-packages'))
        assert response.status_code == 200
        col = [p for p in response.data if p['nationality'] == 'COL']
        assert len(col) == 5
        assert all(p['currency'] == 'COP' for p in col)
        # July 2026 ladder starts with a 1-hour package at 40.000 COP/h.
        assert col[0]['hours'] == 1
        assert float(col[0]['hourly_rate']) == 40000.0

    def test_filters_by_nationality(self, admin_client, mex_package):
        response = admin_client.get(
            reverse('list-admin-hour-packages'), {'nationality': 'MEX'}
        )
        assert response.status_code == 200
        ids = [p['id'] for p in response.data]
        assert mex_package.id in ids
        assert all(p['nationality'] == 'MEX' for p in response.data)
        assert all(p['currency'] == 'USD' for p in response.data)

    def test_rejects_invalid_nationality_filter(self, admin_client):
        response = admin_client.get(
            reverse('list-admin-hour-packages'), {'nationality': 'BRA'}
        )
        assert response.status_code == 400


class TestAdminHourPackageCreate:
    def test_returns_403_for_unauthenticated(self, api_client):
        response = api_client.post(reverse('create-hour-package'), {}, format='json')
        assert response.status_code in (401, 403)

    def test_creates_package_with_derived_currency(self, admin_client):
        payload = {
            'nationality': 'MEX',
            'name_es': 'Paquete Pro MX',
            'name_en': 'Pro Pack MX',
            'hours': 60,
            'hourly_rate': '40.00',
            'discount_percent': 10,
        }
        response = admin_client.post(
            reverse('create-hour-package'), payload, format='json'
        )
        assert response.status_code == 201
        assert response.data['currency'] == 'USD'
        assert HourPackage.objects.filter(
            nationality='MEX', name_es='Paquete Pro MX').count() == 1

    def test_rejects_zero_hours(self, admin_client):
        payload = {
            'nationality': 'COL', 'name_es': 'X', 'name_en': 'X',
            'hours': 0, 'hourly_rate': '90000',
        }
        response = admin_client.post(
            reverse('create-hour-package'), payload, format='json'
        )
        assert response.status_code == 400
        assert 'hours' in response.data

    def test_rejects_discount_above_100(self, admin_client):
        payload = {
            'nationality': 'COL', 'name_es': 'X', 'name_en': 'X',
            'hours': 10, 'hourly_rate': '90000', 'discount_percent': 150,
        }
        response = admin_client.post(
            reverse('create-hour-package'), payload, format='json'
        )
        assert response.status_code == 400
        assert 'discount_percent' in response.data

    def test_rejects_invalid_nationality(self, admin_client):
        payload = {
            'nationality': 'BRA', 'name_es': 'X', 'name_en': 'X',
            'hours': 10, 'hourly_rate': '90000',
        }
        response = admin_client.post(
            reverse('create-hour-package'), payload, format='json'
        )
        assert response.status_code == 400
        assert 'nationality' in response.data


class TestAdminHourPackageRetrieveUpdate:
    def test_returns_403_for_unauthenticated(self, api_client, mex_package):
        url = reverse('update-hour-package', args=[mex_package.id])
        response = api_client.patch(url, {}, format='json')
        assert response.status_code in (401, 403)

    def test_retrieves_detail(self, admin_client, mex_package):
        url = reverse('retrieve-admin-hour-package', args=[mex_package.id])
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.data['name_es'] == 'Paquete Ágil MX'
        assert response.data['currency'] == 'USD'

    def test_partial_update(self, admin_client, mex_package):
        url = reverse('update-hour-package', args=[mex_package.id])
        response = admin_client.patch(
            url, {'hourly_rate': '50.00', 'discount_percent': 5}, format='json'
        )
        assert response.status_code == 200
        mex_package.refresh_from_db()
        assert float(mex_package.hourly_rate) == 50.0
        assert mex_package.discount_percent == 5

    def test_update_returns_404_for_missing(self, admin_client):
        url = reverse('update-hour-package', args=[999999])
        response = admin_client.patch(url, {'hours': 5}, format='json')
        assert response.status_code == 404


class TestAdminHourPackageDelete:
    def test_returns_403_for_unauthenticated(self, api_client, mex_package):
        url = reverse('delete-hour-package', args=[mex_package.id])
        response = api_client.delete(url)
        assert response.status_code in (401, 403)

    def test_deletes_package(self, admin_client, mex_package):
        url = reverse('delete-hour-package', args=[mex_package.id])
        response = admin_client.delete(url)
        assert response.status_code == 204
        assert not HourPackage.objects.filter(pk=mex_package.id).exists()


class TestHourPackageSettings:
    def test_returns_403_for_unauthenticated(self, api_client):
        response = api_client.get(reverse('hour-package-settings'))
        assert response.status_code in (401, 403)

    def test_get_returns_table_default(self, admin_client):
        response = admin_client.get(reverse('hour-package-settings'))
        assert response.status_code == 200
        assert response.data['default_view_mode'] == 'table'

    def test_patch_updates_view_mode(self, admin_client):
        response = admin_client.patch(
            reverse('update-hour-package-settings'),
            {'default_view_mode': 'cards'}, format='json',
        )
        assert response.status_code == 200
        assert HourPackageSettings.load().default_view_mode == 'cards'

    def test_patch_rejects_unknown_mode(self, admin_client):
        response = admin_client.patch(
            reverse('update-hour-package-settings'),
            {'default_view_mode': 'carousel'}, format='json',
        )
        assert response.status_code == 400
        assert 'default_view_mode' in response.data


class TestRestoreDefaultHourPackages:
    def test_returns_403_for_unauthenticated(self, api_client):
        response = api_client.post(
            reverse('restore-default-hour-packages'), {}, format='json'
        )
        assert response.status_code in (401, 403)

    def test_rejects_invalid_nationality(self, admin_client):
        response = admin_client.post(
            reverse('restore-default-hour-packages'),
            {'nationality': 'BRA'}, format='json',
        )
        assert response.status_code == 400

    def test_replaces_catalog_with_defaults(self, admin_client):
        HourPackage.objects.filter(nationality='COL').delete()
        custom = HourPackage.objects.create(
            nationality='COL', name_es='Custom', name_en='Custom',
            hours=7, hourly_rate=99999, discount_percent=1, order=1,
        )
        response = admin_client.post(
            reverse('restore-default-hour-packages'),
            {'nationality': 'COL'}, format='json',
        )
        assert response.status_code == 200
        assert not HourPackage.objects.filter(pk=custom.id).exists()
        col = HourPackage.objects.filter(nationality='COL').order_by('order')
        assert col.count() == 5
        assert col.first().hours == 1
        assert float(col.first().hourly_rate) == 40000.0
        # The response returns the fresh list for the store to swap in.
        assert len(response.data) == 5

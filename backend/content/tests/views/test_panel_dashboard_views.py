"""Tests for content/views/panel_dashboard.py — consolidated dashboard endpoint."""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestPanelDashboard:
    def test_anonymous_is_rejected(self, api_client):
        response = api_client.get(reverse('panel-dashboard'))

        assert response.status_code in (401, 403)

    def test_staff_gets_payload_without_finance(self, admin_client):
        response = admin_client.get(reverse('panel-dashboard'))

        assert response.status_code == 200
        data = response.json()
        assert data['finance'] is None
        assert 'by_status' in data['proposals']
        assert 'tasks' in data['operations']
        assert data['attention'] == []

    def test_superuser_gets_finance_block(self, super_client):
        response = super_client.get(reverse('panel-dashboard'))

        assert response.status_code == 200
        finance = response.json()['finance']
        assert finance is not None
        for key in (
            'liquid_total', 'expected_total', 'liquid_utility',
            'pocket_balance', 'card_debt', 'monthly',
        ):
            assert key in finance

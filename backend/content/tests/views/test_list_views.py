"""
Tests for simple list API views: designs, hostings, products, models3d, portfolio_works.

Covers: GET endpoints returning 200 with serialized data.
"""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


class TestDesignListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('design-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_designs(self, api_client, design):
        response = api_client.get(reverse('design-list'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['title_en'] == 'Modern Dashboard'


class TestHostingListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('hosting-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_hostings(self, api_client, hosting):
        response = api_client.get(reverse('hosting-list'))
        assert response.status_code == 200
        assert len(response.data) == 1


class TestProductListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('product-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_products(self, api_client, product):
        response = api_client.get(reverse('product-list'))
        assert response.status_code == 200
        assert len(response.data) == 1


class TestModel3DListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('model3d-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_models(self, api_client, model_3d):
        response = api_client.get(reverse('model3d-list'))
        assert response.status_code == 200
        assert len(response.data) == 1


class TestPortfolioWorksListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('portfolio-works-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_works(self, api_client, portfolio_work):
        response = api_client.get(reverse('portfolio-works-list'))
        assert response.status_code == 200
        assert len(response.data) == 1

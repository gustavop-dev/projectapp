"""
Tests for contact API views.

Covers: GET /api/contacts/, POST /api/new-contact/ (happy path, validation errors).
"""
import pytest
from unittest.mock import patch
from django.urls import reverse

from content.models import Contact


pytestmark = pytest.mark.django_db


class TestContactListView:
    def test_returns_200_with_empty_list(self, api_client):
        response = api_client.get(reverse('contact-list'))
        assert response.status_code == 200
        assert response.data == []

    def test_returns_all_contacts(self, api_client, contact):
        response = api_client.get(reverse('contact-list'))
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['email'] == 'client@example.com'


class TestNewContactView:
    @patch('content.views.contact.send_email_notification')
    def test_creates_contact_returns_201(self, mock_email, api_client):
        payload = {
            'email': 'new@example.com',
            'phone_number': '+573009999999',
            'subject': 'New project',
            'message': 'I want a website.',
            'budget': '10-20K',
        }
        response = api_client.post(reverse('new-contact'), payload, format='json')
        assert response.status_code == 201
        assert Contact.objects.count() == 1
        assert Contact.objects.first().email == 'new@example.com'
        mock_email.assert_called_once()

    @patch('content.views.contact.send_email_notification')
    def test_creates_contact_without_optional_fields(self, mock_email, api_client):
        payload = {
            'email': 'min@example.com',
            'phone_number': '123',
            'subject': 'Quick question',
        }
        response = api_client.post(reverse('new-contact'), payload, format='json')
        assert response.status_code == 201

    def test_returns_400_with_missing_email(self, api_client):
        payload = {
            'phone_number': '123',
            'subject': 'Test',
        }
        response = api_client.post(reverse('new-contact'), payload, format='json')
        assert response.status_code == 400
        assert 'email' in response.data

    def test_returns_400_with_invalid_email(self, api_client):
        payload = {
            'email': 'not-an-email',
            'phone_number': '123',
            'subject': 'Test',
        }
        response = api_client.post(reverse('new-contact'), payload, format='json')
        assert response.status_code == 400

    @patch('content.views.contact.send_email_notification')
    def test_email_notification_contains_subject(self, mock_email, api_client):
        payload = {
            'email': 'test@test.com',
            'phone_number': '123',
            'subject': 'Important Project',
            'message': 'Details here.',
        }
        api_client.post(reverse('new-contact'), payload, format='json')
        call_args = mock_email.call_args
        assert 'Important Project' in call_args[0][0]

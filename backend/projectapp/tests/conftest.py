"""Fixtures for the CAPTCHA boundary; HTTP is the only mocked service."""
import json
from unittest.mock import patch

import pytest
import requests
from django.contrib.auth import get_user_model

from accounts.models import UserProfile


@pytest.fixture
def captcha_settings(settings):
    settings.RECAPTCHA_ENABLED = True
    settings.RECAPTCHA_SITE_KEY = 'site-key-for-tests'
    settings.RECAPTCHA_SECRET_KEY = 'secret-for-tests'
    settings.RECAPTCHA_ALLOWED_HOSTNAMES = ['testserver']
    return settings


@pytest.fixture
def google_response(captcha_settings):
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps({'success': True, 'hostname': 'testserver'}).encode()
    with patch('projectapp.recaptcha.requests.post', return_value=response) as post:
        yield post


@pytest.fixture
def captcha_user(db):
    user = get_user_model().objects.create_user(
        username='captcha@example.com', email='captcha@example.com',
        password='Test-login-password-1', is_staff=True,
    )
    UserProfile.objects.create(
        user=user, role=UserProfile.ROLE_ADMIN, is_onboarded=True, profile_completed=True,
    )
    return user


class LoginSurface:
    def __init__(self, client, endpoint, user):
        self.client = client
        self.endpoint = endpoint
        self.user = user

    def post(self, token='valid-token', password='Test-login-password-1', **extra):
        payloads = {
            'panel': ('/admin/login/?next=/panel/', {
                'username': self.user.username, 'password': password,
                'g-recaptcha-response': token, 'next': '/panel/',
            }),
            'platform': ('/api/accounts/login/', {
                'email': self.user.email, 'password': password, 'recaptcha_token': token,
            }),
        }
        url, payload = payloads[self.endpoint]
        return self.client.post(url, {**payload, **extra})

    def error_code(self, response):
        if self.endpoint == 'platform':
            return response.json()['code']
        return response.context['form'].non_field_errors().as_data()[0].code


@pytest.fixture(params=['panel', 'platform'])
def login_surface(request, client, captcha_user, google_response):
    return LoginSurface(client, request.param, captcha_user)

"""Tests for the serve_nuxt catch-all view.

Verifies that SPA routes like /panel are served correctly via the
200.html fallback, and that missing fallback files produce actionable
log warnings instead of silent 404s.
"""
import os
import shutil
import tempfile

import pytest
from django.test import RequestFactory, override_settings

from projectapp.views import serve_nuxt


@pytest.fixture
def frontend_dir(tmp_path):
    """Create a temporary frontend directory with a 200.html fallback."""
    spa_html = tmp_path / '200.html'
    spa_html.write_text('<html><body>SPA Shell</body></html>')
    return str(tmp_path)


@pytest.fixture
def frontend_dir_with_prerendered(frontend_dir):
    """Frontend dir that also has a pre-rendered /en-us/index.html."""
    locale_dir = os.path.join(frontend_dir, 'en-us')
    os.makedirs(locale_dir, exist_ok=True)
    with open(os.path.join(locale_dir, 'index.html'), 'w') as f:
        f.write('<html><body>EN-US Home</body></html>')
    return frontend_dir


@pytest.fixture
def frontend_dir_no_fallback(tmp_path):
    """Frontend directory without any fallback HTML files."""
    return str(tmp_path)


@pytest.fixture
def rf():
    """Django RequestFactory."""
    return RequestFactory()


class TestServeNuxtPanelRoute:
    """Tests that /panel SPA routes resolve correctly."""

    def test_panel_route_serves_spa_fallback(self, rf, frontend_dir, settings):
        settings.BASE_DIR = os.path.dirname(frontend_dir)
        # Patch FRONTEND_DIR at module level
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir
        try:
            request = rf.get('/panel')
            response = serve_nuxt(request, path='panel')
            content = b''.join(response.streaming_content).decode()
            assert response.status_code == 200
            assert 'SPA Shell' in content
            assert response['Cache-Control'] == 'no-cache'
        finally:
            views_mod.FRONTEND_DIR = original

    def test_panel_subpath_serves_spa_fallback(self, rf, frontend_dir):
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir
        try:
            request = rf.get('/panel/proposals')
            response = serve_nuxt(request, path='panel/proposals')
            content = b''.join(response.streaming_content).decode()
            assert response.status_code == 200
            assert 'SPA Shell' in content
        finally:
            views_mod.FRONTEND_DIR = original

    def test_panel_deep_subpath_serves_spa_fallback(self, rf, frontend_dir):
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir
        try:
            request = rf.get('/panel/proposals/42/edit')
            response = serve_nuxt(request, path='panel/proposals/42/edit')
            content = b''.join(response.streaming_content).decode()
            assert response.status_code == 200
            assert 'SPA Shell' in content
        finally:
            views_mod.FRONTEND_DIR = original


class TestServeNuxtPrerenderedRoutes:
    """Tests that pre-rendered pages are served directly."""

    def test_prerendered_route_serves_index_html(self, rf, frontend_dir_with_prerendered):
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir_with_prerendered
        try:
            request = rf.get('/en-us/')
            response = serve_nuxt(request, path='en-us')
            content = b''.join(response.streaming_content).decode()
            assert response.status_code == 200
            assert 'EN-US Home' in content
        finally:
            views_mod.FRONTEND_DIR = original


class TestServeNuxtMissingFallback:
    """Tests behavior when 200.html is missing."""

    def test_panel_route_returns_404_when_fallback_missing(self, rf, frontend_dir_no_fallback):
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir_no_fallback
        try:
            request = rf.get('/panel')
            with pytest.raises(Exception) as exc_info:
                serve_nuxt(request, path='panel')
            assert '404' in str(type(exc_info.value).__name__) or 'Http404' in str(type(exc_info.value))
        finally:
            views_mod.FRONTEND_DIR = original

    def test_panel_route_logs_warning_when_fallback_missing(self, rf, frontend_dir_no_fallback, caplog):
        import logging
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir_no_fallback
        try:
            request = rf.get('/panel')
            with caplog.at_level(logging.WARNING, logger='projectapp.views'):
                with pytest.raises(Exception):
                    serve_nuxt(request, path='panel')
            assert 'SPA fallback missing' in caplog.text
            assert '200.html' in caplog.text
        finally:
            views_mod.FRONTEND_DIR = original

    def test_unknown_route_no_warning_when_fallback_missing(self, rf, frontend_dir_no_fallback, caplog):
        """Non-SPA routes should not produce the SPA-specific warning."""
        import logging
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir_no_fallback
        try:
            request = rf.get('/some-random-path')
            with caplog.at_level(logging.WARNING, logger='projectapp.views'):
                with pytest.raises(Exception):
                    serve_nuxt(request, path='some-random-path')
            assert 'SPA fallback missing' not in caplog.text
        finally:
            views_mod.FRONTEND_DIR = original


class TestServeNuxtRootRedirect:
    """Tests root path redirect behavior."""

    def test_root_redirects_to_default_locale(self, rf, frontend_dir):
        import projectapp.views as views_mod
        original = views_mod.FRONTEND_DIR
        views_mod.FRONTEND_DIR = frontend_dir
        try:
            request = rf.get('/')
            response = serve_nuxt(request, path='')
            assert response.status_code == 302
            assert response['Location'] == '/en-us/'
        finally:
            views_mod.FRONTEND_DIR = original

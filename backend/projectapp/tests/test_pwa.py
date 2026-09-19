"""The public PWA routes must serve files rather than Nuxt's HTML fallback."""
import json

import pytest
from django.test import Client


@pytest.fixture
def pwa_build(tmp_path, settings):
    """A generated site containing deliberately distinguishable file contents."""
    settings.BASE_DIR = tmp_path
    build = tmp_path / 'static' / 'frontend'
    build.mkdir(parents=True)
    (build / 'manifest.webmanifest').write_text(json.dumps({'id': '/panel'}))
    (build / 'sw.js').write_text('self.addEventListener("fetch", () => {});')
    (build / '200.html').write_text('<html>SPA fallback</html>')
    return build


@pytest.mark.parametrize(('filename', 'mime'), [
    ('manifest.webmanifest', 'application/manifest+json'),
    ('sw.js', 'application/javascript'),
])
def test_pwa_route_serves_generated_file(pwa_build, filename, mime):
    response = Client().get(f'/{filename}')
    assert response.status_code == 200
    assert response['Content-Type'] == mime
    assert response['Cache-Control'] == 'no-cache'
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert b''.join(response.streaming_content) == (pwa_build / filename).read_bytes()


@pytest.mark.parametrize('filename', ['manifest.webmanifest', 'sw.js'])
def test_missing_pwa_file_returns_not_found(pwa_build, filename):
    (pwa_build / filename).unlink()
    response = Client().get(f'/{filename}')
    assert response.status_code == 404
    assert b'SPA fallback' not in response.content


@pytest.mark.parametrize('filename', ['manifest.webmanifest', 'sw.js'])
def test_pwa_route_rejects_post(pwa_build, filename):
    response = Client().post(f'/{filename}', data='overwrite', content_type='text/plain')
    assert response.status_code == 405
    assert (pwa_build / filename).read_text() != 'overwrite'


@pytest.mark.parametrize('filename', ['manifest.webmanifest', 'sw.js'])
def test_pwa_route_supports_head(pwa_build, filename):
    response = Client().head(f'/{filename}')
    assert response.status_code == 200
    assert response['Content-Length'] == str((pwa_build / filename).stat().st_size)
    assert b''.join(response.streaming_content) == b''

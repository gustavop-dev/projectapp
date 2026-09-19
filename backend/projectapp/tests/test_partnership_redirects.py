from pathlib import Path

import pytest

from projectapp.views import serve_nuxt


@pytest.mark.parametrize(('path', 'destination'), [
    ('es-co/panel/financing', '/es-co/panel/partnership-program'),
    ('en-us/panel/financing', '/en-us/panel/partnership-program'),
    ('es-co/panel/financing/new/', '/es-co/panel/partnership-program/new'),
    ('en-us/panel/financing/42', '/en-us/panel/partnership-program/42'),
    ('panel/financing', '/es-co/panel/partnership-program'),
    ('panel/financing/new', '/es-co/panel/partnership-program/new'),
    ('panel/financing/42', '/es-co/panel/partnership-program/42'),
])
def test_panel_financing_redirects_permanently(rf, path, destination):
    response = serve_nuxt(rf.get(f'/{path}'), path=path)

    assert response.status_code == 301
    assert response['Location'] == destination


def test_panel_redirect_preserves_encoded_query(rf):
    path = 'es-co/panel/financing'
    query = 'tab=agreements&search=A%26B'

    response = serve_nuxt(rf.get(f'/{path}?{query}'), path=path)

    assert response['Location'] == f'/es-co/panel/partnership-program?{query}'


def test_panel_redirect_precedes_stale_html(rf, tmp_path, monkeypatch):
    path = 'es-co/panel/financing'
    stale = Path(tmp_path, path)
    stale.mkdir(parents=True)
    (stale / 'index.html').write_text('<html>Old panel</html>')
    monkeypatch.setattr('projectapp.views.FRONTEND_DIR', str(tmp_path))

    response = serve_nuxt(rf.get(f'/{path}'), path=path)

    assert response.status_code == 301
    assert response['Location'] == '/es-co/panel/partnership-program'

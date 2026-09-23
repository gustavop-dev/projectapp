"""Untrusted packages must never become executable or escape their asset scope."""
import io
import json
import zipfile
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from content.services.linktree_templates.package import normalize_image, read_package
from content.services.linktree_templates.render import render_document
from content.services.linktree_templates.syntax import (
    TemplateError,
    render_mustache,
    validate_sources,
)

HTML = '<main><h1>{{name}}</h1>{{#links}}<a data-link href="{{url}}">{{label}}</a>{{/links}}</main>'
MANIFEST = {'spec': '1.0', 'name': 'Editorial', 'assets': [], 'fonts': [], 'motion': False, 'max_width': 480}


def package(source=HTML, css='', manifest=None, assets=None):
    files = {'template.html': source.encode(), 'template.css': css.encode(), 'manifest.json': json.dumps(manifest or MANIFEST).encode(), **(assets or {})}
    return [(name, SimpleUploadedFile(name, raw)) for name, raw in files.items()]


@pytest.mark.parametrize('source', [
    HTML + '<script>alert(1)</script>',
    HTML + '<img src="{{photo_url}}" onerror="alert(1)">',
    HTML + '<a data-link href="https://evil.example">Entrar</a>',
    HTML + '<iframe srcdoc="anything"></iframe>',
    HTML.replace('{{name}}', '{{{name}}}'),
    HTML.replace('{{name}}', '{{name}}<{{bio}}>'),
])
def test_rejects_executable_markup_and_fixed_destinations(source):
    with pytest.raises(TemplateError) as caught:
        read_package(package(source))
    assert caught.value.issue['severity'] == 'error'
    assert caught.value.issue['file'] == 'template.html'


def test_css_parser_rejects_escaped_external_url_and_reports_line():
    css = '.card {color:red}\n.card {background:u\\72l(https://evil.example/pixel)}'
    with pytest.raises(TemplateError) as caught:
        read_package(package(css=css))
    assert caught.value.issue['file'] == 'template.css'
    assert caught.value.issue['line'] == 2
    assert 'asset(clave)' in str(caught.value)


def test_mustache_escapes_profile_and_resolves_filtered_inverted_sections():
    result = render_mustache('{{name}}{{^photo_url}}<b>{{initials}}</b>{{/photo_url}}{{#links.social}}<a href="{{url}}">{{label}}</a>{{/links.social}}',
                             {'name': '<script>"', 'initials': 'MC', 'links.social': [{'url': 'https://example.com/?a="&b=2', 'label': '<CEO>'}]})
    assert result == '&lt;script&gt;&quot;<b>MC</b><a href="https://example.com/?a=&quot;&amp;b=2">&lt;CEO&gt;</a>'


def test_zip_rejects_traversal_without_extracting(tmp_path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('../template.html', HTML)
        archive.writestr('manifest.json', json.dumps(MANIFEST))
    with pytest.raises(TemplateError, match='rutas absolutas'):
        read_package([('package', SimpleUploadedFile('template.zip', stream.getvalue()))])
    assert not list(tmp_path.iterdir())


def test_svg_removes_active_and_external_content_but_preserves_artwork():
    raw = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4000 2000" onload="bad()"><script>bad()</script><foreignObject/><rect width="100" height="100" fill="red"/><use href="https://evil.example/a.svg#x"/></svg>'
    variants, metadata, changed = normalize_image(raw, 'assets/art.svg')
    assert changed is True
    assert metadata['width'] == 2000
    assert metadata['height'] == 1000
    assert b'<rect' in variants[1]
    assert all(value not in variants[1] for value in (b'script', b'foreignObject', b'onload', b'evil.example'))


def test_png_resizes_without_losing_alpha():
    buffer = io.BytesIO()
    Image.new('RGBA', (2400, 1000), (120, 10, 80, 90)).save(buffer, 'PNG')
    variants, metadata, _ = normalize_image(buffer.getvalue(), 'assets/sticker.png')
    image = Image.open(io.BytesIO(variants[3]))
    assert image.width == metadata['width'] == 2000
    assert image.mode == 'RGBA'
    assert image.getpixel((20, 20))[3] == 90


def test_motion_requires_reduced_motion_and_transform_opacity_only():
    manifest = {**MANIFEST, 'motion': True}
    with pytest.raises(TemplateError, match='reduced-motion'):
        validate_sources(HTML, '.sello {animation:girar 18s infinite}', manifest)
    with pytest.raises(TemplateError, match='Sólo se animan'):
        validate_sources(HTML, '@keyframes girar {to {left:20px}} @media(prefers-reduced-motion:reduce){*{animation:none!important}}', manifest)


def test_renderer_inserts_trusted_icons_and_escapes_profile():
    source = HTML.replace('{{label}}', '<span data-icon="{{icon}}"></span>{{label}}')
    template = SimpleNamespace(html=source, css='a{display:block;min-height:44px}', manifest=MANIFEST)
    profile = {'name': '<script>bad()</script>', 'photo_url': '', 'logo_url': '', 'contact': {'email': '', 'tel': ''},
               'buttons': [{'label': 'Contactar', 'url': 'https://example.com', 'key': '7', 'tier': 'primary', 'icon': 'user-plus', 'kind': 'web'}]}
    version = SimpleNamespace(id=uuid4(), template=template, profile=profile, assets={})
    document = render_document(version)
    assert '<script>bad()' not in document
    assert '&lt;script&gt;' in document
    assert 'data-link-key="7"' in document
    assert '<svg' in document
    assert 'stroke="currentColor"' in document


def test_malformed_asset_role_returns_manifest_error():
    manifest = {**MANIFEST, 'assets': [{'key': 'art', 'file': 'assets/art.png', 'alt': '', 'role': []}]}
    with pytest.raises(TemplateError) as caught:
        read_package(package(manifest=manifest))
    assert caught.value.issue['file'] == 'manifest.json'
    assert str(caught.value) == 'alt o role inválido.'


def test_equal_destinations_keep_each_links_analytics_identity():
    template = SimpleNamespace(html=HTML, css='', manifest=MANIFEST)
    profile = {'name': 'Equipo', 'contact': {'email': '', 'tel': ''}, 'buttons': [
        {'label': 'Principal', 'url': 'https://example.com', 'key': '7', 'tier': 'primary', 'icon': 'globe', 'kind': 'web'},
        {'label': 'Más información', 'url': 'https://example.com', 'key': '8', 'tier': 'row', 'icon': 'globe', 'kind': 'web'},
    ]}
    document = render_document(SimpleNamespace(id=uuid4(), template=template, profile=profile, assets={}))
    assert 'data-link-key="7"' in document
    assert 'data-link-key="8"' in document


def test_nested_link_sections_cannot_expand_without_bound():
    source = '{{#links}}' * 10 + '{{label}}' + '{{/links}}' * 10
    with pytest.raises(TemplateError) as caught:
        render_mustache(source, {'links': [{'label': 'link'}] * 10})
    assert caught.value.issue['code'] == 'template_complexity'

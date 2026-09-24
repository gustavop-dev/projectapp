"""Closed template syntax and actionable author diagnostics."""
import pytest

from content.services.linktree_templates.syntax import TemplateError, parse_mustache, validate_sources
from content.tests.services.test_linktree_template_package import HTML, MANIFEST


@pytest.mark.parametrize(('source', 'message'), [
    ('{{>partial}} {{name}}', 'Sintaxis Mustache no admitida'),
    ('{{#unknown}}{{/unknown}}', 'Sección desconocida'),
    ('{{#links}}{{/name}}', 'Cierre de sección incorrecto'),
    ('{{unknown}}', 'Variable desconocida'),
    ('{{url}}', 'dentro de un bloque de enlaces'),
    ('{{#links}}', 'Falta cerrar la sección'),
    ('{{#name}}' * 21 + '{{/name}}' * 21, 'Demasiados niveles'),
])
def test_invalid_mustache_reports_syntax_error(source, message):
    """Fails if unsupported Mustache syntax is silently accepted."""
    with pytest.raises(TemplateError, match=message) as caught:
        parse_mustache(source)

    assert caught.value.issue['file'] == 'template.html'


@pytest.mark.parametrize(('markup', 'message'), [
    ('<div id="one" id="two"></div>', 'atributos duplicados'),
    ('<div title={{name}}></div>', 'entre comillas'),
    ('<meta name="description" content="custom">', 'plataforma define los metadatos'),
    ('<img>', 'necesita data-asset'),
    ('<div data-action="share"></div>', 'Acción desconocida'),
    ('<!-- {{name}} -->', 'variables no pueden estar en comentarios'),
])
def test_invalid_html_reports_source_line(markup, message):
    """Fails if forbidden markup loses its author-facing location."""
    with pytest.raises(TemplateError, match=message) as caught:
        validate_sources(HTML + '\n' + markup, '', MANIFEST)

    assert caught.value.issue['line'] == 2
    assert caught.value.issue['file'] == 'template.html'


@pytest.mark.parametrize(('css', 'message'), [
    ('@import "https://example.com/style.css";', '@import no está permitido'),
    ('main {behavior: url(#local)}', 'propiedad behavior'),
    ('main {background: image-set("image.png" 1x)}', 'función image-set'),
    ('main {background: asset(missing)}', 'Asset no declarado'),
    ('main {color: {{name}}}', 'CSS no admite variables'),
])
def test_unsafe_css_reports_stylesheet_error(css, message):
    """Fails if CSS can introduce undeclared resources or executable behavior."""
    with pytest.raises(TemplateError, match=message) as caught:
        validate_sources(HTML, css, MANIFEST)

    assert caught.value.issue['file'] == 'template.css'


def test_nested_css_consumes_declared_asset():
    """Fails if assets referenced inside nested CSS are reported unused."""
    manifest = {**MANIFEST, 'assets': [{'key': 'hero', 'file': 'assets/hero.svg', 'alt': ''}]}
    css = '@media(min-width:320px){main{background:linear-gradient(#fff,#000),asset(hero);filter:url("#shadow")}}'

    notices = validate_sources(HTML, css, manifest)

    assert notices == []

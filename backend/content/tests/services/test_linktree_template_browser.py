"""Measured layout regressions; these tests run real headless Chromium."""
from types import SimpleNamespace
from uuid import uuid4

from content.services.linktree_templates.render import render_document
from content.services.linktree_templates.validation import validate_in_browser


def version(css):
    template = SimpleNamespace(html='<main><h1>{{name}}</h1>{{#links}}<a data-link href="{{url}}">{{label}}</a>{{/links}}</main>',
                               css=css, warnings=[], manifest={'fonts': [], 'motion': False, 'max_width': 480})
    profile = {'name': 'Marco Camacho', 'contact': {'email': '', 'tel': ''},
               'buttons': [{'label': 'Visitar sitio', 'url': 'https://example.com', 'key': '1', 'tier': 'primary', 'icon': 'globe', 'kind': 'web'}]}
    row = SimpleNamespace(id=uuid4(), template=template, profile=profile, assets={})
    row.document = render_document(row)
    return row


def test_valid_layout_produces_three_captures(settings):
    row = version('body{background:#fff;color:#111;font-family:sans-serif}main{padding:20px}a{display:flex;align-items:center;min-height:48px;color:#111;background:#fff}')
    report, screenshots = validate_in_browser(row)
    assert report['issues'] == []
    assert set(screenshots) == {'320', '375', '430'}
    from content.storage import get_private_storage
    with get_private_storage().open(screenshots['320'], 'rb') as file:
        assert file.read(8) == b'\x89PNG\r\n\x1a\n'


def test_measures_low_contrast_small_links_and_overflow(settings):
    row = version('body{background:#fff;color:#aaa}main{width:350px}a{color:#aaa;font-size:10px}')
    report, _ = validate_in_browser(row)
    codes = {issue['code'] for issue in report['issues']}
    assert {'contrast', 'touch_target', 'overflow'} <= codes
    assert any(issue['width'] == 320 and issue['code'] == 'overflow' for issue in report['issues'])


def test_continuous_button_motion_is_rejected(settings):
    row = version('body{color:#111;background:#fff}a{display:block;min-height:48px;animation:move 4s infinite}@keyframes move{to{transform:translateX(2px)}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}')
    row.template.manifest['motion'] = True
    report, _ = validate_in_browser(row)
    assert any(issue['code'] == 'continuous_text' for issue in report['issues'])

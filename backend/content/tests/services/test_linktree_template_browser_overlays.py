"""Measured overlay regressions for elements and CSS pseudo-elements."""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from content.services.linktree_templates.render import render_document
from content.services.linktree_templates.validation import validate_in_browser

HTML = (
    '<main><h1>{{name}}</h1>'
    '{{#links}}<a data-link href="{{url}}">{{label}}</a>{{/links}}</main>'
)
BASE_CSS = (
    'body{margin:0;background:#fff;color:#111;font-family:sans-serif}'
    'main{padding:16px}'
    'a{display:flex;align-items:center;min-height:48px;color:#111;background:#fff}'
)


def version(css, *, motion=False):
    """Build a rendered candidate for real-browser validation."""
    template = SimpleNamespace(
        html=HTML,
        css=BASE_CSS + css,
        warnings=[],
        manifest={'fonts': [], 'motion': motion, 'max_width': 480},
    )
    profile = {
        'name': 'Overlay test',
        'contact': {'email': '', 'tel': ''},
        'buttons': [{
            'label': 'Visit site',
            'url': 'https://example.com',
            'key': '1',
            'tier': 'primary',
            'icon': 'globe',
            'kind': 'web',
        }],
    }
    row = SimpleNamespace(id=uuid4(), template=template, profile=profile, assets={})
    row.document = render_document(row)
    return row


def overlay_widths(report):
    """Return viewports where browser geometry found a prohibited overlay."""
    return sorted(
        issue['width']
        for issue in report['issues']
        if issue['code'] == 'fixed_overlay'
    )


@pytest.mark.parametrize('pseudo', ['::before', '::after'], ids=('before', 'after'))
def test_full_viewport_main_pseudo_reports_fixed_overlay_at_every_width(settings, pseudo):
    """Fails if a fixed pseudo-element can cover the viewport without detection."""
    row = version(
        f'main{pseudo}{{content:"";position:fixed;inset:0;background:#fff;z-index:2}}'
    )

    report, _ = validate_in_browser(row)

    assert overlay_widths(report) == [320, 375, 430]


def test_full_viewport_body_pseudo_reports_fixed_overlay_at_every_width(settings):
    """Fails if the document body's fixed pseudo-element is omitted from geometry checks."""
    row = version(
        'body::before{content:"";position:fixed;inset:0;background:#fff;z-index:2}'
    )

    report, _ = validate_in_browser(row)

    assert overlay_widths(report) == [320, 375, 430]


def test_fixed_body_reports_overlay_at_every_width(settings):
    """Fails if the body itself can become a prohibited viewport overlay."""
    row = version('body{position:fixed;inset:0}')

    report, _ = validate_in_browser(row)

    assert overlay_widths(report) == [320, 375, 430]


def test_pseudo_below_twenty_percent_is_accepted(settings):
    """Fails if measured pseudo geometry at the allowed threshold is rejected."""
    row = version(
        'main::before{content:"";position:fixed;left:0;top:0;'
        'width:300px;height:190px;background:#fff}'
    )

    report, _ = validate_in_browser(row)

    assert report['issues'] == []


def test_offscreen_pseudo_uses_clipped_viewport_area(settings):
    """Fails if offscreen pseudo dimensions count instead of their visible clipped area."""
    row = version(
        'main::before{content:"";position:fixed;left:-990px;top:0;'
        'width:1000px;height:1000px;background:#fff}'
    )

    report, _ = validate_in_browser(row)

    assert report['issues'] == []


def test_animated_pseudo_reports_overlay_reached_only_at_late_keyframe(settings):
    """Fails if late transform keyframes let a pseudo-element grow into an overlay."""
    row = version(
        'main::before{content:"";position:fixed;left:0;top:0;width:20px;height:20px;'
        'background:#fff;transform-origin:top left;animation:grow 18s linear infinite}'
        '@keyframes grow{0%,90%{transform:scale(1)}100%{transform:scale(40)}}'
        '@media(prefers-reduced-motion:reduce){main::before{animation:none!important}}',
        motion=True,
    )

    report, _ = validate_in_browser(row)

    assert overlay_widths(report) == [320, 375, 430]

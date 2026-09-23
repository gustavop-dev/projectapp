"""Image density contracts for rendered Linktree template documents."""
import io
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright

from content.services.linktree_templates.package import normalize_image
from content.services.linktree_templates.render import (
    asset_srcset,
    asset_url,
    preview_document,
    public_document,
    render_document,
    snapshot_document,
)

HTML = '<main><img data-asset="hero"><img src="{{photo_url}}"></main>'
PROFILE = {
    'name': 'Image team', 'role': '', 'bio': '', 'company': '', 'badge': '',
    'footer_tagline': '', 'profile_url': '', 'photo_url': '', 'logo_url': '',
    'contact': {'email': '', 'tel': ''}, 'buttons': [], 'pwa_enabled': False,
}


def image_bytes(width):
    stream = io.BytesIO()
    Image.new('RGB', (width, 400), 'blue').save(stream, format='PNG')
    return stream.getvalue()


def row(*, assets, document=''):
    template = SimpleNamespace(
        html=HTML,
        css='img{display:block;width:100%;max-width:600px}',
        manifest={'fonts': [], 'motion': False, 'max_width': 600, 'slots': {}},
        warnings=[],
    )
    return SimpleNamespace(
        id=uuid4(), template=template, profile=dict(PROFILE), assets=assets,
        document=document, linktree=SimpleNamespace(handle='image-team'),
    )


def asset(width, mime='image/webp'):
    return {'width': width, 'mime': mime, 'alt': 'Image', 'paths': {'1': 'one', '2': 'two', '3': 'three'}, 'size': 12}


def serve_image_document(route, document, source_urls, raw):
    if route.request.url == 'https://template.invalid/':
        return route.fulfill(body=document, content_type='text/html')
    if route.request.url in source_urls:
        return route.fulfill(body=raw, content_type='image/png')
    return route.abort()


def test_normalizer_keeps_all_variants_at_actual_width_below_base_limit():
    """Fails if a 600px source is falsely advertised as higher-density pixels."""
    variants, metadata, _ = normalize_image(image_bytes(600), 'hero.png')

    assert metadata['width'] == 600
    assert [Image.open(io.BytesIO(variants[density])).width for density in (1, 2, 3)] == [600, 600, 600]


def test_srcset_deduplicates_600px_raster_at_one_density():
    """Fails if a sub-base raster emits duplicate descriptors for identical pixels."""
    version = row(assets={'hero': asset(600)})

    result = asset_srcset(version, 'hero')

    assert result == f'{asset_url(version, "hero", 1)} 1x'


def test_srcset_uses_actual_descriptors_for_1000px_raster():
    """Fails if a 1000px raster is labelled as a nonexistent 2x or 3x source."""
    version = row(assets={'hero': asset(1000)})

    result = asset_srcset(version, 'hero')

    assert result == (
        f'{asset_url(version, "hero", 1)} 1x, '
        f'{asset_url(version, "hero", 2)} 1.49925037481x'
    )


def test_srcset_exposes_svg_once_at_one_density():
    """Fails if a vector image is duplicated as fake raster density variants."""
    version = row(assets={'hero': asset(2000, 'image/svg+xml')})

    result = asset_srcset(version, 'hero')

    assert result == f'{asset_url(version, "hero", 1)} 1x'


def test_rendered_document_uses_actual_srcset_for_decorative_and_profile_images():
    """Fails if photo slots or decorative assets retain misleading density descriptors."""
    version = row(assets={'hero': asset(1000), 'slot-photo': asset(600)})

    document = render_document(version)

    assert f'srcset="{asset_url(version, "hero", 1)} 1x, {asset_url(version, "hero", 2)} 1.49925037481x"' in document
    assert f'srcset="{asset_url(version, "slot-photo", 1)} 1x"' in document


@pytest.mark.parametrize('device_scale_factor', [1, 2, 3])
def test_600px_source_keeps_320px_layout_at_each_device_pixel_ratio(device_scale_factor):
    """Fails if a small source reduces the stable 320px image size at high DPR."""
    version = row(assets={'hero': asset(600)})
    version.template.html = '<main><img data-asset="hero"></main>'
    version.template.css = 'img{display:block;max-width:100%;height:auto}'
    version.document = render_document(version)
    raw = image_bytes(600)
    source_url = f'https://template.invalid{asset_url(version, "hero", 1)}'
    source_urls = {f'https://template.invalid{asset_url(version, "hero", density)}' for density in (1, 2, 3)}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(device_scale_factor=device_scale_factor)
        page = context.new_page()
        page.set_viewport_size({'width': 320, 'height': 500})
        page.route('**/*', lambda route: serve_image_document(route, version.document, source_urls, raw))
        page.goto('https://template.invalid/', wait_until='load')
        page.locator('img').evaluate('(image) => image.decode()')
        box = page.locator('img').bounding_box()
        current_src = page.locator('img').evaluate('(image) => image.currentSrc')
        natural_width = page.locator('img').evaluate('(image) => image.naturalWidth')
        context.close()
        browser.close()

    assert box['width'] == pytest.approx(320, abs=0.1)
    assert natural_width == 600
    assert current_src == source_url


def test_snapshot_document_repairs_legacy_srcset_without_persisting_document_change():
    """Fails if preview repair changes the immutable stored HTML snapshot."""
    version = row(assets={'hero': asset(1000)})
    legacy = ', '.join(f'{asset_url(version, "hero", density)} {density}x' for density in (1, 2, 3))
    version.document = f'<img srcset="{legacy}">'

    repaired = snapshot_document(version)

    assert f'{asset_url(version, "hero", 2)} 1.49925037481x' in repaired
    assert version.document == f'<img srcset="{legacy}">'


def test_preview_document_repairs_and_signs_legacy_srcset():
    """Fails if a legacy preview keeps fake density URLs or loses its signed access token."""
    version = row(assets={'hero': asset(1000)})
    legacy = ', '.join(f'{asset_url(version, "hero", density)} {density}x' for density in (1, 2, 3))
    version.document = f'<img srcset="{legacy}">'

    document = preview_document(version)

    assert f'{asset_url(version, "hero", 2)}?preview=' in document
    assert '1.49925037481x' in document
    assert version.document == f'<img srcset="{legacy}">'


def test_public_document_repairs_legacy_srcset_without_mutating_snapshot():
    """Fails if public rendering retains stale density descriptors or rewrites stored HTML."""
    version = row(assets={'hero': asset(1000)})
    legacy = ', '.join(f'{asset_url(version, "hero", density)} {density}x' for density in (1, 2, 3))
    version.document = f'<html><body><img srcset="{legacy}"></body></html>'

    document = public_document(version, 'test-nonce')

    assert f'{asset_url(version, "hero", 2)} 1.49925037481x' in document
    assert version.document == f'<html><body><img srcset="{legacy}"></body></html>'

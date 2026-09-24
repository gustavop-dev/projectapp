"""Per-card image library: verbatim URLs, key snapshots and file retention."""
import pytest

from content.models import LinktreeAsset
from content.services.linktree_templates import library, service
from content.services.linktree_templates.package import read_package
from content.services.linktree_templates.syntax import TemplateError
from content.storage import get_private_storage
from content.tests.services.test_linktree_template_package import (
    HTML,
    MANIFEST,
    package,
)
from content.tests.views.test_linktree_template_views import (
    image_upload,
    make_template,
    make_tree,
    make_version,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def tree_with_hero():
    tree = make_tree('library-card')
    asset, _ = library.upload_asset(tree, 'hero', 'Fondo', image_upload('hero.png'))
    return tree, asset


def test_verbatim_library_url_is_normalized_to_the_key(tree_with_hero):
    """Fails if the URL returned by the upload cannot be pasted straight into the design."""
    tree, asset = tree_with_hero
    source = HTML + f'<img src="{asset.url}"><div style="background:url({asset.url})"></div>'
    css = f'main{{background:url("{asset.url}")}}'

    manifest, html, css_out, images, notices = read_package(package(source, css), library.library_map(tree))

    assert '<img data-asset="hero">' in html and 'asset(hero)' in html
    assert css_out == 'main{background:asset(hero)}'
    assert manifest['library_assets'] == ['hero']
    assert images == {} and notices == []


def test_library_key_can_be_referenced_directly_and_unknown_keys_fail(tree_with_hero):
    """Fails if data-asset accepts undeclared keys or ignores library ones."""
    tree, _ = tree_with_hero

    manifest, *_ = read_package(package(HTML + '<img data-asset="hero">'), library.library_map(tree))
    assert manifest['library_assets'] == ['hero']

    with pytest.raises(TemplateError) as caught:
        read_package(package(HTML + '<img data-asset="missing">'), library.library_map(tree))
    assert 'missing' in str(caught.value)


def test_package_key_cannot_shadow_a_library_key(tree_with_hero):
    """Fails if an ambiguous key silently picks one of two images."""
    tree, _ = tree_with_hero
    manifest = {**MANIFEST, 'assets': [{'key': 'hero', 'file': 'assets/hero.png', 'alt': ''}]}
    files = package(HTML + '<img data-asset="hero">', manifest=manifest, assets={'assets/hero.png': image_upload().read()})

    with pytest.raises(TemplateError) as caught:
        read_package(files, library.library_map(tree))

    assert caught.value.issue['code'] == 'library_key_clash'


def test_author_cannot_declare_library_assets_in_the_manifest(tree_with_hero):
    """Fails if a manifest can claim library keys the sources never use."""
    tree, _ = tree_with_hero

    with pytest.raises(TemplateError) as caught:
        read_package(package(manifest={**MANIFEST, 'library_assets': ['hero']}), library.library_map(tree))

    assert caught.value.issue['file'] == 'manifest.json'
    manifest, *_ = read_package(package(), library.library_map(tree))
    assert manifest['library_assets'] == []


def test_candidate_snapshots_the_current_library_image(tree_with_hero, monkeypatch):
    """Fails if a version does not carry its own copy of the library files."""
    tree, asset = tree_with_hero
    monkeypatch.setattr(service, 'queue_validation', lambda version_id: None)
    template = make_template(tree)
    template.html += '<img data-asset="hero">'
    template.manifest['library_assets'] = ['hero']
    template.save(update_fields=['html', 'manifest'])

    version = service.create_version(tree, template)

    assert version.assets['hero']['paths'] == asset.image['paths']
    assert f'/api/linktrees/templates/{version.pk}/assets/hero/1/' in version.document


def test_missing_library_image_blocks_the_candidate(tree_with_hero):
    """Fails if a template referencing a deleted library image reaches the browser."""
    tree, _ = tree_with_hero
    template = make_template(tree)
    template.manifest['library_assets'] = ['hero']
    library.delete_asset(tree, 'hero')

    with pytest.raises(TemplateError) as caught:
        service.create_version(tree, template)

    assert caught.value.issue['code'] == 'missing_library_asset'
    assert tree.template_versions.count() == 0


def test_replacing_keeps_files_referenced_by_a_version(tree_with_hero, django_capture_on_commit_callbacks):
    """Fails if replacing a library image deletes files a published snapshot still serves."""
    tree, asset = tree_with_hero
    old_path = asset.image['paths']['1']
    version = make_version(tree, make_template(tree), status='valid', published=True)
    version.assets = {'hero': asset.image}
    version.save(update_fields=['assets'])

    with django_capture_on_commit_callbacks(execute=True):
        replaced, _ = library.upload_asset(tree, 'hero', 'Nuevo', image_upload('new.png'))

    assert replaced.pk == asset.pk and replaced.image['paths']['1'] != old_path
    assert get_private_storage().exists(old_path)
    assert LinktreeAsset.objects.filter(linktree=tree).count() == 1


def test_deleting_an_unreferenced_image_removes_its_files(tree_with_hero, django_capture_on_commit_callbacks):
    """Fails if orphaned library files linger in private storage."""
    tree, asset = tree_with_hero
    paths = list(asset.image['paths'].values())

    with django_capture_on_commit_callbacks(execute=True):
        library.delete_asset(tree, 'hero')

    assert not tree.assets.exists()
    assert not any(get_private_storage().exists(path) for path in paths)


@pytest.mark.parametrize('key', ['Hero', 'slot-photo', '', 'a' * 41])
def test_invalid_keys_are_rejected(key):
    """Fails if a key the template syntax cannot reference is accepted."""
    tree = make_tree('library-invalid-key')

    with pytest.raises(TemplateError) as caught:
        library.upload_asset(tree, key, '', image_upload())

    assert caught.value.issue['code'] == 'invalid_key'
    assert not tree.assets.exists()

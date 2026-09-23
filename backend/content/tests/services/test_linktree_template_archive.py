"""Package boundaries and private asset rollback."""
import io
import json
import stat
import zipfile
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from content.services.linktree_templates.package import asset_batch, read_package, store_image
from content.services.linktree_templates.syntax import TemplateError
from content.storage import get_private_storage
from content.tests.services.test_linktree_template_package import HTML, MANIFEST, package


def archive_upload(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return [('package', SimpleUploadedFile('template.zip', stream.getvalue()))]


def test_zip_with_enclosing_directory_loads_declared_artwork():
    """Fails if folder-wrapped ZIP uploads cannot load their declared images."""
    manifest = {**MANIFEST, 'assets': [{'key': 'hero', 'file': 'assets/hero.svg', 'alt': 'Banner'}]}
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><rect width="20" height="10"/></svg>'
    files = archive_upload([
        ('design/', ''), ('design/assets/', ''),
        ('design/manifest.json', json.dumps(manifest)),
        ('design/template.html', HTML + '<img data-asset="hero">'),
        ('design/assets/hero.svg', svg),
    ])

    parsed, source, css, images, notices = read_package(files)

    assert parsed['name'] == 'Editorial'
    assert source == HTML + '<img data-asset="hero">'
    assert css == ''
    assert images['hero'][1]['width'] == 20
    assert images['hero'][1]['alt'] == 'Banner'
    assert notices == []


def test_zip_rejects_symlink_entries():
    """Fails if a ZIP symlink is accepted as a template resource."""
    member = zipfile.ZipInfo('assets/link.svg')
    member.create_system = 3
    member.external_attr = (stat.S_IFLNK | 0o777) << 16

    with pytest.raises(TemplateError, match='enlaces simbólicos') as caught:
        read_package(archive_upload([(member, '/private/file')]))

    assert caught.value.issue['file'] == 'manifest.json'


def test_zip_rejects_decompressed_size_over_limit():
    """Fails if compressed content bypasses the four-megabyte limit."""
    files = archive_upload([('template.html', b'x' * (4 * 1024 * 1024 + 1))])

    with pytest.raises(TemplateError, match='descomprimido supera 4 MB') as caught:
        read_package(files)

    assert caught.value.issue['file'] == 'manifest.json'


def test_invalid_zip_reports_package_error():
    """Fails if malformed ZIP bytes escape as an internal server error."""
    files = [('package', SimpleUploadedFile('template.zip', b'not a zip'))]

    with pytest.raises(TemplateError, match='ZIP inválido') as caught:
        read_package(files)

    assert caught.value.issue['file'] == 'manifest.json'


def test_duplicate_upload_path_is_rejected():
    """Fails if a duplicate file silently replaces an earlier upload."""
    files = package() + [('template.html', SimpleUploadedFile('template.html', b'replacement'))]

    with pytest.raises(TemplateError, match='Archivo repetido: template.html') as caught:
        read_package(files)

    assert caught.value.issue['code'] == 'invalid_template'


def test_oversized_source_reports_its_filename():
    """Fails if a source larger than 200 KB enters the HTML parser."""
    files = package(source=HTML + 'x' * (200 * 1024))

    with pytest.raises(TemplateError, match='supera 200 KB') as caught:
        read_package(files)

    assert caught.value.issue['file'] == 'template.html'


def test_undeclared_package_file_is_rejected():
    """Fails if undeclared files can be smuggled into an accepted package."""
    files = package(assets={'extra.txt': b'unlisted'})

    with pytest.raises(TemplateError, match='coincidir con los assets') as caught:
        read_package(files)

    assert caught.value.issue['file'] == 'manifest.json'


def test_asset_transaction_removes_files_after_failure(settings):
    """Fails if a failed template upload leaves private asset files behind."""
    storage = get_private_storage()

    with pytest.raises(ValueError, match='invalid profile'):
        with asset_batch():
            asset = store_image({1: b'one', 2: b'two', 3: b'three'}, {'mime': 'image/webp'})
            raise ValueError('invalid profile')

    assert [storage.exists(path) for path in asset['paths'].values()] == [False, False, False]


def test_storage_failure_removes_earlier_image_variant(settings):
    """Fails if saving a later density leaks the earlier stored variant."""
    storage = get_private_storage()
    saved_paths = []
    save = storage.save

    def fail_second_variant(name, content, **kwargs):
        if saved_paths:
            raise OSError('disk full')
        path = save(name, content, **kwargs)
        saved_paths.append(path)
        return path

    with patch.object(storage, 'save', side_effect=fail_second_variant):
        with pytest.raises(OSError, match='disk full'):
            store_image({1: b'one', 2: b'two', 3: b'three'}, {'mime': 'image/webp'})

    assert len(saved_paths) == 1
    assert storage.exists(saved_paths[0]) is False

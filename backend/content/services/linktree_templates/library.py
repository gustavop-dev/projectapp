"""Per-Linktree image library: upload once, reference from any template.

Library files live in private storage exactly like package assets. A version
snapshots the library image it uses, so a later replacement or deletion of the
library entry never changes a published page; files are only removed from
storage when no version snapshot references the key anymore.
"""
import copy

from content.models import LinktreeAsset
from content.storage import get_private_storage
from django.db import transaction

from .package import IMAGE_LIMIT, KEY, normalize_image, store_image
from .syntax import issue


def asset_url(tree_id, key):
    return f'/api/linktrees/admin/{tree_id}/assets/{key}/'


def library_map(tree):
    """URL → key for every library image, used to normalize verbatim references."""
    return {asset_url(tree.pk, key): key for key in tree.assets.values_list('key', flat=True)}


def asset_row(asset):
    image = asset.image
    return {
        'key': asset.key,
        'alt': asset.alt,
        'url': asset.url,
        'format': image.get('format'),
        'mime': image.get('mime'),
        'width': image.get('width'),
        'height': image.get('height'),
        'size': image.get('size'),
        'created_at': asset.created_at,
        'updated_at': asset.updated_at,
        'markup': {'html': f'<img data-asset="{asset.key}">', 'css': f'asset({asset.key})'},
    }


def referenced(tree, key):
    return tree.template_versions.filter(assets__has_key=key).exists()


def delete_files(image):
    storage = get_private_storage()
    for path in image.get('paths', {}).values():
        storage.delete(path)


def upload_asset(tree, key, alt, uploaded):
    key = (key or '').strip()
    if not KEY.fullmatch(key) or key.startswith('slot-'):
        issue('Clave inválida: minúsculas, números, guion o guion bajo, hasta 40 caracteres.', 'library', code='invalid_key')
    if not isinstance(alt, str) or len(alt) > 500:
        issue('alt debe ser texto de hasta 500 caracteres.', 'library', code='invalid_alt')
    variants, metadata, changed = normalize_image(uploaded.read(IMAGE_LIMIT + 1), uploaded.name)
    image = store_image(variants, {**metadata, 'alt': alt})
    with transaction.atomic():
        previous = tree.assets.select_for_update().filter(key=key).first()
        if previous:
            old_image = previous.image
            previous.alt, previous.image = alt, image
            previous.save(update_fields=['alt', 'image', 'updated_at'])
            asset = previous
            if not referenced(tree, key):
                transaction.on_commit(lambda: delete_files(old_image))
        else:
            asset = LinktreeAsset.objects.create(linktree=tree, key=key, alt=alt, image=image)
    return asset, changed


def delete_asset(tree, key):
    with transaction.atomic():
        asset = tree.assets.select_for_update().filter(key=key).first()
        if asset is None:
            issue('No existe esa imagen en la biblioteca del Linktree.', 'library', code='missing_library_asset')
        image = asset.image
        asset.delete()
        if not referenced(tree, key):
            transaction.on_commit(lambda: delete_files(image))


def snapshot_library(tree, template):
    """Copy the current library images a template uses into a candidate version."""
    keys = list(template.manifest.get('library_assets', []))
    if not keys:
        return {}
    rows = {asset.key: asset for asset in tree.assets.filter(key__in=keys)}
    missing = [key for key in keys if key not in rows]
    if missing:
        issue(f'Faltan en la biblioteca de imágenes de este Linktree: {", ".join(missing)}.',
              'profile', code='missing_library_asset')
    return {key: copy.deepcopy(rows[key].image) for key in keys}

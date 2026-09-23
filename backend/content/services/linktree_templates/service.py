"""Panel operations. Uploads never change the currently published snapshot."""
import copy
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from content.models import Linktree, LinktreeTemplate, LinktreeTemplateVersion
from .package import normalize_image, read_package, store_image
from .render import profile_data, profile_digest, render_document
from .syntax import TemplateError, issue

logger = logging.getLogger(__name__)


def client_id(tree):
    return tree.project.client_id if tree.project_id else None


def available_templates(tree):
    own = Q(owner=tree)
    client = client_id(tree)
    if client:
        own |= Q(client_id=client, is_shared=True)
    return LinktreeTemplate.objects.filter(own)


def expire_pending(tree):
    pending = tree.template_versions.filter(status='pending')
    pending.filter(created_at__lt=timezone.now() - timedelta(minutes=10)).update(
        status='invalid', report={'issues': [{'severity': 'error', 'code': 'validation_timeout',
                                             'message': 'La validación expiró. Vuelve a validar.'}]})
    return pending


def check_pending(tree):
    if expire_pending(tree).exists():
        issue('Espera a que termine la validación en curso.', 'profile', code='validation_pending')


def upload_package(tree, files):
    manifest, source, css, images, notices = read_package(files)
    assets = {key: store_image(*image) for key, image in images.items()}
    return LinktreeTemplate.objects.create(owner=tree, client_id=client_id(tree), name=manifest['name'],
                                           manifest=manifest, html=source, css=css, assets=assets, warnings=notices)


def snapshot_slots(tree, template):
    assets = {}
    for slot, field in [('photo', tree.avatar), ('logo', tree.logo)]:
        contract = template.manifest['slots'].get(slot, {})
        if not field:
            if contract.get('required'):
                issue(f'Debes cargar la imagen de {slot} antes de validar.', 'profile', code='required_slot')
            continue
        with field.open('rb') as stream:
            variants, metadata, _ = normalize_image(stream.read(5 * 1024 * 1024 + 1), field.name, limit=5 * 1024 * 1024)
        if min(metadata['width'], metadata['height']) < contract.get('min_px', 0):
            issue(f'La imagen {slot} debe medir al menos {contract["min_px"]} px por lado.', 'profile', code='slot_size')
        if contract.get('format') and metadata['format'] not in contract['format'] and not (metadata['format'] in {'jpg', 'jpeg'} and {'jpg', 'jpeg'} & set(contract['format'])):
            issue(f'Formato de {slot} incompatible con el manifest.', 'profile', code='slot_format')
        # The aspect contract is applied by CSS to the image, preserving the
        # source pixels and allowing the author to choose object-fit/position.
        metadata['alt'] = tree.display_name if slot == 'photo' else tree.vcard_org
        assets[f'slot-{slot}'] = store_image(variants, metadata)
    return assets


def create_version(tree, template, previous=None, replacement=None, reset_key=None):
    check_pending(tree)
    profile = profile_data(tree)
    assets = copy.deepcopy(previous.assets if previous else template.assets)
    overrides = list(previous.overrides if previous else [])
    for key in ('slot-photo', 'slot-logo'):
        assets.pop(key, None)
    if replacement or reset_key:
        key = replacement[0] if replacement else reset_key
        if key not in template.manifest['editable_assets']:
            issue('Esta imagen no es editable.', 'manifest.json')
        if replacement:
            uploaded = replacement[1]
            variants, metadata, _ = normalize_image(uploaded.read(800 * 1024 + 1), uploaded.name)
            assets[key] = store_image(variants, {**metadata, 'alt': template.assets[key].get('alt', '')})
            if key not in overrides:
                overrides.append(key)
        else:
            assets[key] = copy.deepcopy(template.assets[key])
            overrides = [value for value in overrides if value != key]
    assets.update(snapshot_slots(tree, template))
    with transaction.atomic():
        # Serialize candidate creation for this card; two uploads cannot bypass
        # the one-in-flight validation limit.
        locked = Linktree.objects.select_for_update().get(pk=tree.pk)
        check_pending(locked)
        version = LinktreeTemplateVersion.objects.create(linktree=tree, template=template, assets=assets,
                                                         overrides=overrides, profile=profile, profile_digest=profile_digest(profile))
        version.document = render_document(version)
        version.save(update_fields=['document'])
        transaction.on_commit(lambda: queue_validation(version.pk))
    return version


def queue_validation(version_id):
    from content.tasks import validate_linktree_template
    try:
        validate_linktree_template(str(version_id))
    except Exception:
        logger.exception('Could not enqueue Linktree template validation')
        LinktreeTemplateVersion.objects.filter(pk=version_id, status='pending').update(
            status='invalid', report={'issues': [{'severity': 'error', 'code': 'validator_unavailable',
                                                 'message': 'La validación no está disponible. Vuelve a validar.'}]})


def run_validation(version_id):
    from .validation import validate_in_browser
    version = LinktreeTemplateVersion.objects.select_related('template').filter(pk=version_id, status='pending').first()
    if not version:
        return
    try:
        report, screenshots = validate_in_browser(version)
        status = 'invalid' if any(i['severity'] == 'error' for i in report['issues']) else 'valid'
    except Exception:
        logger.exception('Linktree browser validation failed for %s', version_id)
        report = {'issues': [{'severity': 'error', 'code': 'validator_unavailable',
                             'message': 'No se pudo completar la validación visual. Reintenta o consulta al administrador.'}]}
        screenshots, status = {}, 'invalid'
    LinktreeTemplateVersion.objects.filter(pk=version_id, status='pending').update(status=status, report=report, screenshots=screenshots)


def publish_version(tree, version):
    with transaction.atomic():
        tree = Linktree.objects.select_for_update().prefetch_related('buttons').get(pk=tree.pk)
        if version.linktree_id != tree.pk or version.status != 'valid':
            issue('La versión debe superar todas las validaciones antes de publicar.', 'profile', code='not_validated')
        if profile_digest(profile_data(tree)) != version.profile_digest:
            issue('Los datos del perfil cambiaron. Vuelve a validar antes de publicar.', 'profile', code='profile_changed')
        version.published_at = version.published_at or timezone.now()
        version.save(update_fields=['published_at'])
        tree.active_template_version = version
        tree.save(update_fields=['active_template_version', 'updated_at'])
    return version


def version_summary(version, tree):
    base = f'/api/linktrees/admin/{tree.pk}/templates/{version.pk}'
    return {'id': str(version.pk), 'template_id': str(version.template_id), 'name': version.template.name,
            'status': version.status, 'created_at': version.created_at, 'published_at': version.published_at,
            'active': tree.active_template_version_id == version.pk,
            'issues': version.report.get('issues', []), 'page_bytes': version.report.get('page_bytes'),
            'preview_url': f'{base}/preview/',
            'screenshots': {width: f'{base}/screenshots/{width}/' for width in version.screenshots},
            'editable_assets': [{'key': key, 'url': f'{base}/asset-preview/{key}/', 'overridden': key in version.overrides}
                                for key in version.template.manifest['editable_assets']]}

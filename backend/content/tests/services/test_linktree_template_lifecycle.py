"""Candidate version state transitions and profile image requirements."""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from content.models import LinktreeTemplateVersion
from content.services.linktree_templates.service import (
    check_pending, create_version, expire_pending, publish_version, queue_validation,
)
from content.services.linktree_templates.syntax import TemplateError
from content.storage import get_private_storage
from content.tests.views.test_linktree_template_views import image_upload, make_template, make_tree, make_version

pytestmark = pytest.mark.django_db


def test_pending_candidate_blocks_second_validation():
    """Fails if overlapping validations can create multiple pending candidates."""
    tree = make_tree('pending-candidate')
    make_version(tree, make_template(tree), status='pending')

    with pytest.raises(TemplateError) as caught:
        check_pending(tree)

    assert caught.value.issue['code'] == 'validation_pending'


@freeze_time('2026-09-23 10:11:00')
def test_expired_candidate_releases_validation_slot():
    """Fails if a timed-out validation indefinitely prevents another upload."""
    tree = make_tree('expired-candidate')
    candidate = make_version(tree, make_template(tree), status='pending')
    LinktreeTemplateVersion.objects.filter(pk=candidate.pk).update(
        created_at=datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc),
    )

    pending = expire_pending(tree)

    candidate.refresh_from_db()
    assert pending.count() == 0
    assert candidate.status == 'invalid'
    assert candidate.report['issues'][0]['code'] == 'validation_timeout'


@pytest.mark.parametrize('slot', ['photo', 'logo'])
def test_required_profile_image_prevents_candidate_creation(slot):
    """Fails if a required absent profile image reaches browser validation."""
    tree = make_tree('required-image')
    template = make_template(tree)
    template.manifest['slots'] = {slot: {'required': True}}

    with pytest.raises(TemplateError) as caught:
        create_version(tree, template)

    assert caught.value.issue['code'] == 'required_slot'
    assert tree.template_versions.count() == 0


@pytest.mark.parametrize(('contract', 'code'), [
    ({'min_px': 100}, 'slot_size'),
    ({'format': ['jpeg']}, 'slot_format'),
])
def test_incompatible_profile_image_prevents_candidate_creation(contract, code):
    """Fails if image dimensions or format bypass the author's slot contract."""
    tree = make_tree('incompatible-image')
    tree.avatar.save('portrait.png', image_upload())
    template = make_template(tree)
    template.manifest['slots'] = {'photo': contract}

    with pytest.raises(TemplateError) as caught:
        create_version(tree, template)

    assert caught.value.issue['code'] == code
    assert tree.template_versions.count() == 0


def test_candidate_snapshots_profile_image_in_private_storage():
    """Fails if the rendered photo still depends on the mutable profile upload."""
    tree = make_tree('photo-snapshot', display_name='Editorial Team')
    tree.avatar.save('portrait.png', image_upload())
    template = make_template(tree)
    template.manifest['slots'] = {'photo': {'min_px': 20, 'format': ['png']}}
    template.html += '<img src="{{photo_url}}">'

    candidate = create_version(tree, template)

    photo = candidate.assets['slot-photo']
    assert photo['mime'] == 'image/webp'
    assert photo['alt'] == 'Editorial Team'
    assert get_private_storage().exists(photo['paths']['1']) is True
    assert candidate.status == 'pending'
    assert f'/api/linktrees/templates/{candidate.pk}/assets/slot-photo/1/' in candidate.document


def test_reset_asset_creates_original_snapshot():
    """Fails if resetting an override mutates history or keeps the replacement."""
    tree = make_tree('reset-asset')
    template = make_template(tree, editable=True)
    previous = make_version(tree, template, overrides=['hero'])
    previous.assets = {'hero': {'alt': 'Replacement'}}
    previous.save(update_fields=['assets'])

    candidate = create_version(tree, template, previous=previous, reset_key='hero')

    assert candidate.assets['hero'] == template.assets['hero']
    assert candidate.overrides == []
    previous.refresh_from_db()
    assert previous.assets == {'hero': {'alt': 'Replacement'}}
    assert previous.overrides == ['hero']


def test_reset_undeclared_asset_is_rejected():
    """Fails if an editor can reset an asset absent from the editable contract."""
    tree = make_tree('undeclared-asset')
    template = make_template(tree)

    with pytest.raises(TemplateError, match='no es editable') as caught:
        create_version(tree, template, reset_key='missing')

    assert caught.value.issue['file'] == 'manifest.json'


def test_queue_outage_invalidates_pending_candidate():
    """Fails if a worker enqueue failure leaves validation permanently pending."""
    tree = make_tree('queue-outage')
    candidate = make_version(tree, make_template(tree), status='pending')

    with patch('content.tasks.validate_linktree_template', side_effect=ConnectionError('queue unavailable')):
        queue_validation(candidate.pk)

    candidate.refresh_from_db()
    assert candidate.status == 'invalid'
    assert candidate.report['issues'][0]['code'] == 'validator_unavailable'


@pytest.mark.parametrize('status', ['pending', 'invalid'])
def test_unvalidated_candidate_cannot_replace_publication(status):
    """Fails if publication can bypass a pending or failed visual validation."""
    tree = make_tree('unvalidated-publication')
    template = make_template(tree)
    active = make_version(tree, template, published=True)
    tree.active_template_version = active
    tree.save(update_fields=['active_template_version'])
    candidate = make_version(tree, template, status=status)

    with pytest.raises(TemplateError) as caught:
        publish_version(tree, candidate)

    assert caught.value.issue['code'] == 'not_validated'
    tree.refresh_from_db()
    assert tree.active_template_version_id == active.pk

"""Service failure handling for Linktree template browser validation."""
import pytest

from content.models import Linktree, LinktreeTemplate, LinktreeTemplateVersion
from content.services.linktree_templates.service import run_validation

pytestmark = pytest.mark.django_db


def test_run_validation_marks_candidate_invalid_when_browser_is_unavailable(monkeypatch):
    """Fails if a browser outage leaves a pending template version blocking later uploads."""
    tree = Linktree.objects.create(handle='validator-outage', name='Validator outage')
    template = LinktreeTemplate.objects.create(
        owner=tree, name='Editorial', manifest={'editable_assets': []},
        html='<main>{{name}}</main>', assets={},
    )
    version = LinktreeTemplateVersion.objects.create(
        linktree=tree, template=template, profile={}, profile_digest='0' * 64,
    )
    monkeypatch.setattr(
        'content.services.linktree_templates.validation.validate_in_browser',
        lambda candidate: (_ for _ in ()).throw(RuntimeError('Chromium unavailable')),
    )

    run_validation(version.pk)

    version.refresh_from_db()
    assert version.status == 'invalid'
    assert version.report['issues'][0]['code'] == 'validator_unavailable'

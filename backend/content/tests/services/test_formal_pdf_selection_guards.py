"""Guards for the formal PDF's frozen scope and preparation lifecycle."""
import hashlib
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from freezegun import freeze_time
from pypdf import PdfReader

from content.models import (
    ProposalFormalization,
    ProposalFormalizationFile,
    ProposalSection,
)
from content.services.formalization_content import FormalizationError
from content.services.proposal_email_service import ProposalEmailService
from content.services.proposal_formalization_service import (
    document_bytes,
    prepare,
    send_preparation,
    source_hash,
)
from content.tests.services import (
    test_proposal_formalization_service as service_fixtures,
)

pytestmark = pytest.mark.django_db
formalization_payload = service_fixtures.formalization_payload
formalization_proposal = service_fixtures.formalization_proposal


def _pdf_text(raw):
    return '\n'.join(page.extract_text() or '' for page in PdfReader(BytesIO(raw)).pages)


@freeze_time('2026-09-24 12:00:00')
def test_formal_commercial_pdf_keeps_saved_conditions_without_catalog_reseed(
    monkeypatch, formalization_proposal,
):
    """Fails if a formal PDF replaces its saved scope conditions from the catalog."""
    ProposalSection.objects.create(
        proposal=formalization_proposal,
        section_type='commercial_conditions',
        title='Condiciones comerciales',
        order=4,
        content_json={
            'hourPackagesMode': 'auto',
            'scopeParagraphs': ['SAVED_FORMAL_SCOPE_CONDITION'],
        },
    )
    catalog_reseed = Mock(side_effect=AssertionError(
        'formal PDF must not reseed the catalog',
    ))
    monkeypatch.setattr(
        'content.services.proposal_pdf_service.seed_commercial_conditions_from_catalog',
        catalog_reseed,
    )

    rendered = _pdf_text(document_bytes(formalization_proposal, 'commercial'))

    assert 'SAVED_FORMAL_SCOPE_CONDITION' in rendered
    catalog_reseed.assert_not_called()


@freeze_time('2026-09-24 12:00:00')
def test_formal_technical_pdf_excludes_unselected_module_requirement(
    formalization_proposal,
):
    """Fails if an optional module's technical requirement leaks into the formal PDF."""
    requirements = formalization_proposal.sections.get(section_type='functional_requirements')
    requirements.content_json['additionalModules'] = [{
        'id': 'priority-support',
        'title': 'Soporte prioritario',
        'is_calculator_module': True,
        'selected': False,
        'default_selected': False,
        'price_percent': 10,
        'items': [{
            'id': 'priority-channel',
            'name': 'Canal prioritario',
            'description': 'Soporte adicional.',
        }],
    }]
    requirements.save(update_fields=['content_json'])
    technical = formalization_proposal.sections.get(section_type='technical_document')
    technical.content_json['epics'][0]['requirements'].append({
        'flowKey': 'OPTIONAL_FLOW_99',
        'title': 'OPTIONAL_REQUIREMENT',
        'description': 'No pertenece al alcance confirmado.',
        'linked_module_ids': ['module-priority-support'],
    })
    technical.save(update_fields=['content_json'])

    rendered = _pdf_text(document_bytes(formalization_proposal, 'technical'))

    assert 'ORD-01' in rendered
    assert 'create-order' in rendered
    assert 'OPTIONAL_FLOW_99' not in rendered
    assert 'OPTIONAL_REQUIREMENT' not in rendered


@freeze_time('2026-09-24 12:00:00')
def test_send_rejects_a_preparation_after_its_section_title_changes(
    mailoutbox, formalization_proposal, admin_user, formalization_payload,
):
    """Fails if an edited formal section title can bypass stale-preparation review."""
    preparation = prepare(formalization_proposal, admin_user, formalization_payload)
    section = formalization_proposal.sections.get(section_type='investment')
    section.title = 'Inversión actualizada'
    section.save(update_fields=['title'])

    with pytest.raises(FormalizationError) as error:
        send_preparation(preparation)

    assert error.value.code == 'stale_preparation'
    assert error.value.status == 409
    assert len(mailoutbox) == 0


@freeze_time('2026-09-24 12:00:00')
def test_send_legacy_preparation_delivers_its_frozen_bytes(
    mailoutbox, formalization_proposal, admin_user, formalization_payload, monkeypatch,
):
    """Fails if a pre-versioned preparation regenerates its frozen attachment during delivery."""
    legacy_payload = {
        **formalization_payload,
        'documents': ['commercial'],
        'from_email': ProposalEmailService._get_from_email(),
    }
    preparation = ProposalFormalization.objects.create(
        proposal=formalization_proposal,
        created_by=admin_user,
        payload=legacy_payload,
        source_hash=source_hash(formalization_proposal, legacy_payload),
        html_body='<p>Legacy preview</p>',
        text_body='Legacy preview',
        expires_at=timezone.now() + timedelta(hours=1),
    )
    frozen_bytes = b'%PDF-legacy-frozen-commercial-bytes'
    attachment = ProposalFormalizationFile.objects.create(
        preparation=preparation,
        key='commercial',
        filename='legacy-commercial.pdf',
        description='Propuesta comercial formal',
        mime_type='application/pdf',
        sha256=hashlib.sha256(frozen_bytes).hexdigest(),
        size=len(frozen_bytes),
    )
    attachment.file.save(attachment.filename, ContentFile(frozen_bytes), save=True)
    section = formalization_proposal.sections.get(section_type='investment')
    section.title = 'Inversión editada después del envío legado'
    section.save(update_fields=['title'])
    document_generation = Mock(side_effect=AssertionError(
        'delivery must use the frozen attachment',
    ))
    monkeypatch.setattr(
        'content.services.proposal_formalization_service.document_bytes',
        document_generation,
    )

    delivered = send_preparation(preparation)

    assert delivered.status == ProposalFormalization.Status.SENT
    assert mailoutbox[0].attachments[0].filename == 'legacy-commercial.pdf'
    assert mailoutbox[0].attachments[0].content == frozen_bytes
    document_generation.assert_not_called()

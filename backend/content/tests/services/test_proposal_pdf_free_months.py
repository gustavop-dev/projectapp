"""The free-month gift block in the commercial PDF.

Its visibility used to be an undocumented pair of conditions — a non-zero
count AND a non-empty note — that disagreed with the public web view, which
showed the block on the count alone and supplied its own default copy. So a
proposal left at the default (count 1, empty note) showed the gift on the web
and silently dropped it from the PDF. Nothing covered that.

These tests pin the rule the two surfaces now share: the explicit
``freeMonthsVisible`` flag decides, and the copy is resolved for both.
"""
import io
from decimal import Decimal

import pytest
from django.utils import timezone
from pypdf import PdfReader

from content.models import BusinessProposal, ProposalSection
from content.services.pdf_utils import _register_fonts
from content.services.proposal_pdf_service import ProposalPdfService

GIFT_LABEL = 'REGALO'
CUSTOM_NOTE = 'Te regalamos noventa dias de hosting sin costo.'


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


def _proposal_with_hosting(hosting_plan, language='es'):
    proposal = BusinessProposal.objects.create(
        title='Free Months PDF',
        client_name='Cliente Regalo',
        client_email='regalo@example.com',
        language=language,
        total_investment=Decimal('10000000'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=20),
    )
    ProposalSection.objects.create(
        proposal=proposal, section_type='greeting', title='Saludo', order=0,
        is_enabled=True, content_json={'clientName': proposal.client_name},
    )
    ProposalSection.objects.create(
        proposal=proposal, section_type='investment', title='Inversión', order=1,
        is_enabled=True,
        content_json={
            'title': 'Inversión',
            'totalInvestment': '$10.000.000',
            'currency': 'COP',
            'paymentOptions': [{'label': 'Pago único', 'description': '$10.000.000'}],
            'hostingPlan': {
                'title': 'Hosting, Mantenimiento y Soporte',
                'description': 'Infraestructura administrada.',
                'hostingPercent': 60,
                **hosting_plan,
            },
        },
    )
    return proposal


def _pdf_text(proposal):
    pdf = ProposalPdfService.generate(proposal)
    assert len(pdf) > 1000
    return '\n'.join(
        (page.extract_text() or '') for page in PdfReader(io.BytesIO(pdf)).pages
    )


@pytest.mark.django_db
def test_visible_flag_renders_the_gift_callout():
    text = _pdf_text(_proposal_with_hosting({
        'freeMonths': 1, 'freeMonthsVisible': True, 'freeMonthNote': CUSTOM_NOTE,
    }))
    assert GIFT_LABEL in text
    assert 'noventa dias de hosting' in text


@pytest.mark.django_db
def test_unchecked_flag_drops_the_block_even_with_months_and_copy():
    """The count no longer keeps the block alive once the box is unchecked."""
    text = _pdf_text(_proposal_with_hosting({
        'freeMonths': 3, 'freeMonthsVisible': False, 'freeMonthNote': CUSTOM_NOTE,
    }))
    assert GIFT_LABEL not in text
    assert 'noventa dias de hosting' not in text


@pytest.mark.django_db
def test_empty_note_now_prints_the_default_copy():
    """The old web/PDF divergence: this used to render nothing at all."""
    text = _pdf_text(_proposal_with_hosting({
        'freeMonths': 1, 'freeMonthNote': '',
    }))
    assert GIFT_LABEL in text
    assert 'hosting es gratis' in text


@pytest.mark.django_db
def test_english_proposal_prints_the_english_default():
    text = _pdf_text(
        _proposal_with_hosting({'freeMonths': 1, 'freeMonthNote': ''}, language='en'),
    )
    assert GIFT_LABEL in text
    assert 'hosting is free' in text


@pytest.mark.django_db
def test_legacy_zero_count_without_the_flag_stays_hidden():
    """Proposals that used zero to hide the block keep it hidden."""
    text = _pdf_text(_proposal_with_hosting({'freeMonths': 0, 'freeMonthNote': ''}))
    assert GIFT_LABEL not in text
    assert 'hosting es gratis' not in text

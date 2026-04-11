"""Tests for technical-only PDF generation."""

from unittest.mock import patch

import pytest

from content.models import ProposalSection
from content.services.technical_document_pdf import (
    _nonempty_str,
    _row_any,
    generate_technical_document_pdf,
)


# ===========================================================================
# _nonempty_str helper
# ===========================================================================

def test_nonempty_str_returns_truthy_for_nonempty_string():
    assert _nonempty_str('hello')


def test_nonempty_str_returns_falsy_for_whitespace_only():
    assert not _nonempty_str('   ')


def test_nonempty_str_returns_false_for_non_string():
    assert _nonempty_str(42) is False


# ===========================================================================
# _row_any helper
# ===========================================================================

def test_row_any_returns_true_when_any_key_has_nonempty_value():
    assert _row_any({'layer': 'Backend', 'technology': ''}, ('layer', 'technology'))


def test_row_any_returns_false_for_empty_dict():
    assert not _row_any({}, ('layer',))


def test_row_any_returns_false_for_non_dict():
    assert not _row_any('not a dict', ('layer',))


def test_row_any_returns_false_when_all_values_empty():
    assert not _row_any({'layer': '', 'technology': '   '}, ('layer', 'technology'))


# ===========================================================================
# generate_technical_document_pdf — guard clauses
# ===========================================================================

@pytest.mark.django_db
def test_returns_none_when_no_technical_document_section(sent_proposal):
    out = generate_technical_document_pdf(sent_proposal)

    assert out is None


@pytest.mark.django_db
def test_returns_none_when_section_is_disabled(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=False,
        content_json={'purpose': 'Should not appear.'},
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is None


@pytest.mark.django_db
def test_returns_none_when_exception_occurs(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={'purpose': 'Test.'},
    )

    with patch(
        'content.services.technical_document_pdf._register_fonts',
        side_effect=RuntimeError('font error'),
    ):
        out = generate_technical_document_pdf(sent_proposal)

    assert out is None


# ===========================================================================
# generate_technical_document_pdf — module filter integration
# ===========================================================================

@pytest.mark.django_db
def test_generate_invokes_module_filter_with_selected_modules(sent_proposal):
    """Technical PDF applies filter_technical_document_by_module_selection."""
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={'purpose': 'Purpose line for PDF.'},
    )
    with patch(
        'content.services.technical_document_filter.filter_technical_document_by_module_selection',
    ) as mock_filter:
        mock_filter.side_effect = lambda doc, sel: doc
        out = generate_technical_document_pdf(
            sent_proposal, selected_modules=['module-1', 'group-2'],
        )
        mock_filter.assert_called_once()
        assert mock_filter.call_args[0][1] == ['module-1', 'group-2']
        assert out is not None
        assert out[:5] == b'%PDF-'


# ===========================================================================
# generate_technical_document_pdf — section content branches
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_stack_and_architecture(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'stack': [
                {'layer': 'Backend', 'technology': 'Django', 'rationale': 'Mature'},
                {'layer': '', 'technology': '', 'rationale': ''},  # empty row — skipped
            ],
            'architecture': {
                'summary': 'Microservices architecture.',
                'diagramNote': 'See attached diagram.',
                'patterns': [
                    {'component': 'API Gateway', 'pattern': 'Gateway', 'description': 'Routes traffic'},
                ],
            },
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


@pytest.mark.django_db
def test_generates_pdf_with_data_model_and_growth(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'dataModel': {
                'summary': 'Relational model.',
                'relationships': 'One-to-many user/project.',
                'entities': [
                    {'name': 'User', 'description': 'Platform user', 'keyFields': 'id, email'},
                ],
            },
            'growthReadiness': {
                'summary': 'Horizontal scaling.',
                'strategies': [
                    {'dimension': 'Database', 'preparation': 'Read replicas', 'evolution': 'Sharding'},
                ],
            },
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


@pytest.mark.django_db
def test_generates_pdf_with_epics_and_full_requirements(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'epics': [
                {
                    'title': 'User Management',
                    'description': 'Handles user lifecycle.',
                    'requirements': [
                        {
                            'title': 'Login',
                            'description': 'OAuth2 login',
                            'configuration': 'Google provider',
                            'usageFlow': 'User clicks login button',
                            'priority': 'High',
                        },
                        {
                            'title': 'Registration',
                            'description': 'Sign-up flow',
                            'configuration': '',
                            'usageFlow': '',
                        },
                    ],
                },
                {
                    'title': '',  # epic with no title, only reqs
                    'description': '',
                    'requirements': [
                        {'title': 'Dashboard', 'description': 'Main view', 'flowKey': 'main-flow'},
                    ],
                },
            ],
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


@pytest.mark.django_db
def test_generates_pdf_with_api_and_integrations(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'apiSummary': 'RESTful API with JWT.',
            'apiDomains': [
                {'domain': 'Auth', 'summary': 'Authentication endpoints'},
            ],
            'integrations': {
                'notes': 'All integrations are optional.\nCan be added later.',
                'included': [
                    {'service': 'Stripe', 'provider': 'Stripe Inc', 'connection': 'SDK'},
                ],
                'excluded': [
                    {'service': 'Legacy CRM', 'reason': 'Out of scope'},
                ],
            },
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


@pytest.mark.django_db
def test_generates_pdf_with_environments_security_performance(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'environmentsNote': 'Three-tier environment.',
            'environments': [
                {'name': 'Production', 'purpose': 'Live users', 'url': 'https://app.example.com'},
            ],
            'security': [
                {'aspect': 'Authentication', 'implementation': 'JWT + MFA'},
            ],
            'performanceQuality': {
                'metrics': [
                    {'metric': 'Latency', 'target': '<200ms', 'howMeasured': 'Datadog'},
                ],
                'practices': [
                    {'strategy': 'Caching', 'description': 'Redis for hot data'},
                ],
            },
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


@pytest.mark.django_db
def test_generates_pdf_with_backups_quality_decisions(sent_proposal):
    ProposalSection.objects.create(
        proposal=sent_proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json={
            'backupsNote': 'Daily automated backups to S3.',
            'quality': {
                'dimensions': [
                    {'dimension': 'Reliability', 'evaluates': 'Uptime', 'standard': '99.9%'},
                ],
                'testTypes': [
                    {'type': 'Unit', 'validates': 'Business logic', 'tool': 'pytest', 'whenRun': 'CI'},
                ],
                'criticalFlowsNote': 'Login and checkout are critical.',
            },
            'decisions': [
                {'decision': 'Use PostgreSQL', 'alternative': 'MySQL', 'reason': 'JSONB support'},
            ],
        },
    )

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'

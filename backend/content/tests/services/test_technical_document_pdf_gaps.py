"""Tests for uncovered sections in technical_document_pdf.py.

Covers:
- Section 1: purpose (nonempty)
- Section 7: API (apiSummary + apiDomains)
- Section 8: integrations (included, excluded, notes)
- Section 9: environments
- Section 10: security
- Section 11: performanceQuality (metrics + practices)
- Section 12: backups
- Section 13: quality (dimensions, testTypes, criticalFlowsNote)
- Section 14: decisions
- architecture arch_note branch (line 165-167)
- dataModel dm_rel (relationships) branch (line 193-196)
- epics with configuration + usageFlow in req description (lines 282-288)
"""
from decimal import Decimal

import pytest

from content.models import BusinessProposal, ProposalSection
from content.services.technical_document_pdf import generate_technical_document_pdf


@pytest.fixture
def sent_proposal(db):
    from django.utils import timezone
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Technical Document Gaps Test',
        client_name='Gaps Inc',
        total_investment=Decimal('10000.00'),
        status='sent',
        sent_at=now,
        expires_at=now + timezone.timedelta(days=30),
    )


def _make_section(proposal, content_json):
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type='technical_document',
        title='Technical',
        order=0,
        is_enabled=True,
        content_json=content_json,
    )


# ===========================================================================
# Section 1 — purpose
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_purpose_section(sent_proposal):
    """Section 1 'Propósito' is rendered when purpose text is non-empty."""
    _make_section(sent_proposal, {'purpose': 'Build an e-commerce platform for SMEs.'})

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 7 — API (apiSummary + apiDomains)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_api_section(sent_proposal):
    """Section 7 'API' is rendered with summary and domain rows."""
    _make_section(sent_proposal, {
        'apiSummary': 'RESTful API with JWT authentication.',
        'apiDomains': [
            {'domain': 'Auth', 'summary': 'Login, token refresh, logout'},
            {'domain': 'Projects', 'summary': 'CRUD for projects'},
        ],
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 8 — integrations (included, excluded, notes)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_integrations_section(sent_proposal):
    """Section 8 'Integraciones' renders included, excluded, and notes."""
    _make_section(sent_proposal, {
        'integrations': {
            'included': [
                {'service': 'Stripe', 'provider': 'Stripe Inc', 'connection': 'REST API'},
            ],
            'excluded': [
                {'service': 'PayPal', 'reason': 'Not required in MVP'},
            ],
            'notes': 'All integrations require API key rotation every 90 days.',
        },
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 9 — environments
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_environments_section(sent_proposal):
    """Section 9 'Ambientes' is rendered with note and env rows."""
    _make_section(sent_proposal, {
        'environmentsNote': 'All environments use containerized deployments.',
        'environments': [
            {'name': 'Production', 'purpose': 'Live traffic', 'url': 'https://app.example.com'},
            {'name': 'Staging', 'purpose': 'QA testing', 'url': 'https://staging.example.com'},
        ],
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 10 — security
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_security_section(sent_proposal):
    """Section 10 'Seguridad' is rendered with security rows."""
    _make_section(sent_proposal, {
        'security': [
            {'aspect': 'Authentication', 'implementation': 'JWT with refresh tokens'},
            {'aspect': 'CSRF', 'implementation': 'Django middleware'},
        ],
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 11 — performanceQuality (metrics + practices)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_performance_quality_section(sent_proposal):
    """Section 11 'Rendimiento' is rendered with metrics and practices."""
    _make_section(sent_proposal, {
        'performanceQuality': {
            'metrics': [
                {'metric': 'Response time', 'target': '<200ms', 'howMeasured': 'APM tool'},
            ],
            'practices': [
                {'strategy': 'Caching', 'description': 'Redis for session data'},
            ],
        },
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 12 — backups
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_backups_section(sent_proposal):
    """Section 12 'Backups' is rendered when backupsNote is non-empty."""
    _make_section(sent_proposal, {
        'backupsNote': 'Daily full backups with 30-day retention policy.',
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 13 — quality (dimensions, testTypes, criticalFlowsNote)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_quality_section(sent_proposal):
    """Section 13 'Calidad' is rendered with dimensions, test types, and critical flows."""
    _make_section(sent_proposal, {
        'quality': {
            'dimensions': [
                {'dimension': 'Reliability', 'evaluates': 'Uptime', 'standard': '99.9%'},
            ],
            'testTypes': [
                {'type': 'Unit tests', 'validates': 'Business logic', 'tool': 'pytest'},
            ],
            'criticalFlowsNote': 'Login, checkout, and order confirmation.',
        },
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Section 14 — decisions
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_decisions_section(sent_proposal):
    """Section 14 'Decisiones' is rendered with decision rows."""
    _make_section(sent_proposal, {
        'decisions': [
            {'decision': 'Use PostgreSQL', 'alternative': 'MySQL', 'reason': 'Better JSON support'},
        ],
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Architecture note branch (arch_note → lines 165-167)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_architecture_note(sent_proposal):
    """arch_note in architecture renders Nota paragraph."""
    _make_section(sent_proposal, {
        'architecture': {
            'summary': 'Monolithic for MVP.',
            'diagramNote': 'See diagram in Figma.',
        },
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# DataModel relationships branch (dm_rel → lines 193-196)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_data_model_relationships(sent_proposal):
    """dm_rel in dataModel renders Relaciones subtitle."""
    _make_section(sent_proposal, {
        'dataModel': {
            'summary': 'Normalized relational schema.',
            'relationships': 'Users have many projects; projects have many deliverables.',
        },
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'


# ===========================================================================
# Epics with q_conf and q_flow branches (lines 281-288)
# ===========================================================================

@pytest.mark.django_db
def test_generates_pdf_with_epics_configuration_and_usage_flow(sent_proposal):
    """Requirement with configuration and usageFlow renders Config/Flujo desc lines."""
    _make_section(sent_proposal, {
        'epics': [
            {
                'title': 'Authentication',
                'requirements': [
                    {
                        'title': 'User Login',
                        'description': 'Standard credential login.',
                        'configuration': 'Uses Google OAuth2 provider.',
                        'usageFlow': 'User navigates to /login, submits form, receives JWT.',
                    },
                ],
            },
        ],
    })

    out = generate_technical_document_pdf(sent_proposal)

    assert out is not None
    assert out[:5] == b'%PDF-'

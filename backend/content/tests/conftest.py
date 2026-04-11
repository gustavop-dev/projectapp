"""Shared pytest fixtures for the content app test suite.

Provides reusable fixtures for API clients, model instances,
and authenticated users following the project testing standards.
"""
import sys
from decimal import Decimal
from types import ModuleType
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from django.core.files.base import ContentFile

from content.models import (
    BlogPost,
    BusinessProposal,
    CompanySettings,
    Contact,
    ContractTemplate,
    PortfolioWork,
    ProposalDocument,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
    ProposalShareLink,
)

User = get_user_model()


# ── Global mocks ──

@pytest.fixture(autouse=True)
def _skip_mx_validation(monkeypatch):
    """Bypass DNS MX lookups in all tests, even when dnspython is unavailable."""
    if 'dns' not in sys.modules:
        dns_module = ModuleType('dns')
        dns_resolver_module = ModuleType('dns.resolver')
        dns_exception_module = ModuleType('dns.exception')

        class _DummyResolver:
            lifetime = 2.0

            def resolve(self, *_args, **_kwargs):
                return []

        dns_resolver_module.Resolver = _DummyResolver
        dns_resolver_module.NoAnswer = type('NoAnswer', (Exception,), {})
        dns_resolver_module.NXDOMAIN = type('NXDOMAIN', (Exception,), {})
        dns_resolver_module.NoNameservers = type('NoNameservers', (Exception,), {})
        dns_exception_module.Timeout = type('Timeout', (Exception,), {})

        dns_module.resolver = dns_resolver_module
        dns_module.exception = dns_exception_module

        monkeypatch.setitem(sys.modules, 'dns', dns_module)
        monkeypatch.setitem(sys.modules, 'dns.resolver', dns_resolver_module)
        monkeypatch.setitem(sys.modules, 'dns.exception', dns_exception_module)

    with patch('content.utils.check_domain_mx', return_value=True):
        yield


# ── API Clients ──

@pytest.fixture
def api_client():
    """Unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Staff user for admin-gated endpoints."""
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    """Authenticated DRF API client with admin (staff) privileges."""
    api_client.force_authenticate(user=admin_user)
    return api_client


# ── Content Model Fixtures ──

@pytest.fixture
def contact(db):
    """A sample contact message."""
    return Contact.objects.create(
        email='client@example.com',
        phone_number='+573001234567',
        subject='Project inquiry',
        message='I need a web application.',
        budget='5-10K',
    )


@pytest.fixture
def portfolio_work(db):
    """A sample portfolio work entry (without actual image file)."""
    return PortfolioWork.objects.create(
        title_en='Client Portal',
        title_es='Portal de Cliente',
        project_url='https://example.com/client-portal',
        category_title_en='Web Application',
        category_title_es='Aplicación Web',
    )


@pytest.fixture
def published_portfolio_work(db):
    """A published portfolio work with content_json."""
    return PortfolioWork.objects.create(
        title_en='MOOSER Hotel',
        title_es='MOOSER Hotel: Experiencia digital',
        excerpt_en='Digital experience for an alpine hotel.',
        excerpt_es='Experiencia digital para un hotel alpino.',
        project_url='https://mooser-hotel.com',
        content_json_es={
            'problem': {'title': 'El Desafío', 'description': 'Desc ES.', 'highlights': ['H1']},
            'solution': {'title': 'Solución', 'description': 'Sol ES.', 'highlights': ['S1']},
            'results': {'title': 'Resultados', 'description': 'Res ES.', 'highlights': ['R1'], 'testimonial_video_url': ''},
        },
        content_json_en={
            'problem': {'title': 'The Challenge', 'description': 'Desc EN.', 'highlights': ['H1']},
            'solution': {'title': 'Solution', 'description': 'Sol EN.', 'highlights': ['S1']},
            'results': {'title': 'Results', 'description': 'Res EN.', 'highlights': ['R1'], 'testimonial_video_url': ''},
        },
        is_published=True,
    )


@pytest.fixture
def draft_portfolio_work(db):
    """An unpublished (draft) portfolio work."""
    return PortfolioWork.objects.create(
        title_en='Secret Project',
        title_es='Proyecto Secreto',
        project_url='https://example.com/secret',
        is_published=False,
    )


@pytest.fixture
def blog_post(db):
    """A published blog post with bilingual content."""
    return BlogPost.objects.create(
        title_es='Tendencias de IA en 2026',
        title_en='AI Trends in 2026',
        excerpt_es='Un resumen de las tendencias más importantes.',
        excerpt_en='A summary of the most important trends.',
        content_es='<p>Contenido completo en español.</p>',
        content_en='<p>Full content in English.</p>',
        sources=[{'name': 'OpenAI', 'url': 'https://openai.com'}],
        is_published=True,
        published_at=timezone.now(),
    )


@pytest.fixture
def draft_blog_post(db):
    """An unpublished (draft) blog post."""
    return BlogPost.objects.create(
        title_es='Borrador de artículo',
        title_en='Draft article',
        excerpt_es='Extracto del borrador.',
        excerpt_en='Draft excerpt.',
        content_es='<p>Contenido borrador.</p>',
        content_en='<p>Draft content.</p>',
        is_published=False,
    )


@pytest.fixture
def blog_post_with_json(db):
    """A published blog post with structured JSON content."""
    return BlogPost.objects.create(
        title_es='Post con JSON estructurado',
        title_en='Post with structured JSON',
        excerpt_es='Resumen del post JSON.',
        excerpt_en='JSON post excerpt.',
        content_json_es={
            'intro': 'Introducción en español.',
            'sections': [
                {'heading': 'Sección 1', 'content': 'Contenido de la sección 1.'},
                {'heading': 'Sección 2', 'list': ['Item A', 'Item B']},
            ],
            'conclusion': 'Conclusión.',
            'cta': 'Contáctanos.',
        },
        content_json_en={
            'intro': 'Introduction in English.',
            'sections': [
                {'heading': 'Section 1', 'content': 'Section 1 content.'},
            ],
            'conclusion': 'Conclusion.',
            'cta': 'Contact us.',
        },
        category='technology',
        read_time_minutes=8,
        is_featured=True,
        is_published=True,
        published_at=timezone.now(),
    )


@pytest.fixture
def proposal(db):
    """A sample business proposal in draft status."""
    return BusinessProposal.objects.create(
        title='Web Application Development',
        client_name='Acme Corp',
        client_email='contact@acme.com',
        client_phone='+573001234567',
        language='es',
        total_investment=Decimal('15000.00'),
        currency='COP',
        status='draft',
        expires_at=timezone.now() + timezone.timedelta(days=30),
        reminder_days=5,
        discount_percent=20,
        project_type='webapp',
        market_type='b2b',
    )


@pytest.fixture
def sent_proposal(db):
    """A proposal that has been sent to the client."""
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Mobile App Development',
        client_name='Beta Inc',
        client_email='info@beta.com',
        client_phone='+14155551234',
        language='en',
        total_investment=Decimal('25000.00'),
        currency='USD',
        status='sent',
        sent_at=now,
        last_activity_at=now,
        expires_at=now + timezone.timedelta(days=15),
        project_type='webapp',
        market_type='saas',
    )


@pytest.fixture
def expired_proposal(db):
    """A proposal that has expired."""
    return BusinessProposal.objects.create(
        title='Expired Project',
        client_name='Old Client',
        client_email='old@client.com',
        language='es',
        total_investment=Decimal('5000.00'),
        currency='COP',
        status='expired',
        expires_at=timezone.now() - timezone.timedelta(days=1),
    )


@pytest.fixture
def rejected_proposal(db):
    """A proposal that has been rejected by the client."""
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Rejected Project',
        client_name='Declined Client',
        client_email='declined@client.com',
        language='es',
        total_investment=Decimal('8000.00'),
        currency='COP',
        status='rejected',
        rejection_reason='presupuesto alto',
        sent_at=now - timezone.timedelta(days=5),
        first_viewed_at=now - timezone.timedelta(days=3),
        view_count=2,
        responded_at=now - timezone.timedelta(days=1),
        last_activity_at=now - timezone.timedelta(days=1),
        expires_at=now + timezone.timedelta(days=10),
        project_type='website',
        market_type='services',
    )


@pytest.fixture
def viewed_proposal(db):
    """A proposal that has been viewed by the client."""
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Viewed Project',
        client_name='Viewer Client',
        client_email='viewer@client.com',
        language='es',
        total_investment=Decimal('12000.00'),
        currency='COP',
        status='viewed',
        sent_at=now - timezone.timedelta(days=3),
        first_viewed_at=now - timezone.timedelta(hours=6),
        view_count=4,
        last_activity_at=now - timezone.timedelta(hours=6),
        expires_at=now + timezone.timedelta(days=20),
        project_type='ecommerce',
        market_type='b2c',
    )


@pytest.fixture
def negotiating_proposal(db):
    """A proposal in negotiation — client accepted with changes."""
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Negotiating Project',
        client_name='Negotiator Client',
        client_email='negotiator@client.com',
        language='es',
        total_investment=Decimal('18000.00'),
        currency='COP',
        status='negotiating',
        sent_at=now - timezone.timedelta(days=8),
        first_viewed_at=now - timezone.timedelta(days=5),
        view_count=6,
        responded_at=now - timezone.timedelta(days=1),
        last_activity_at=now - timezone.timedelta(days=1),
        expires_at=now + timezone.timedelta(days=12),
        project_type='webapp',
        market_type='b2b',
    )


@pytest.fixture
def accepted_proposal(db):
    """A proposal that has been accepted."""
    now = timezone.now()
    return BusinessProposal.objects.create(
        title='Accepted Project',
        client_name='Accepted Client',
        client_email='accepted@client.com',
        language='es',
        total_investment=Decimal('20000.00'),
        currency='COP',
        status='accepted',
        sent_at=now - timezone.timedelta(days=10),
        first_viewed_at=now - timezone.timedelta(days=7),
        view_count=8,
        responded_at=now - timezone.timedelta(days=2),
        last_activity_at=now - timezone.timedelta(days=2),
        expires_at=now + timezone.timedelta(days=10),
        project_type='webapp',
        market_type='b2b',
    )


@pytest.fixture
def share_link(db, sent_proposal):
    """A share link for a sent proposal."""
    return ProposalShareLink.objects.create(
        proposal=sent_proposal,
        shared_by_name='Alice',
        shared_by_email='alice@company.com',
    )


@pytest.fixture
def proposal_section(db, proposal):
    """A sample proposal section."""
    return ProposalSection.objects.create(
        proposal=proposal,
        section_type='greeting',
        title='Welcome',
        order=0,
        is_enabled=True,
        content_json={'heading': 'Welcome to our proposal'},
    )


@pytest.fixture
def requirement_group(db, proposal):
    """A sample requirement group."""
    return ProposalRequirementGroup.objects.create(
        proposal=proposal,
        group_id='views',
        title='Views',
        description='Frontend views and pages.',
        order=0,
    )


@pytest.fixture
def requirement_item(db, requirement_group):
    """A sample requirement item."""
    return ProposalRequirementItem.objects.create(
        group=requirement_group,
        item_id='dashboard-view',
        icon='✅',
        name='Dashboard View',
        description='Main dashboard with analytics.',
        options=[],
        fields=[],
        order=0,
    )


# ── Contract & Document Fixtures ──

@pytest.fixture
def contract_template(db):
    """A default contract template with placeholders."""
    return ContractTemplate.objects.create(
        name='Standard Contract',
        content_markdown=(
            '# CONTRATO DE PRESTACION DE SERVICIOS\n\n'
            'Entre {client_full_name}, CC {client_cedula}, y '
            '{contractor_full_name}, CC {contractor_cedula}.\n\n'
            'Ciudad: {contract_city}. Fecha: {contract_date}.'
        ),
        is_default=True,
    )


@pytest.fixture
def proposal_document(db, negotiating_proposal):
    """A user-uploaded proposal document."""
    doc = ProposalDocument.objects.create(
        proposal=negotiating_proposal,
        document_type=ProposalDocument.DOC_TYPE_LEGAL_ANNEX,
        title='Legal annex',
        is_generated=False,
    )
    doc.file.save('legal_annex.pdf', ContentFile(b'%PDF-1.4 fake'), save=True)
    return doc


@pytest.fixture
def generated_contract_document(db, negotiating_proposal):
    """A system-generated contract PDF document."""
    doc = ProposalDocument.objects.create(
        proposal=negotiating_proposal,
        document_type=ProposalDocument.DOC_TYPE_CONTRACT,
        title='Contrato de desarrollo de software',
        is_generated=True,
    )
    doc.file.save('contract.pdf', ContentFile(b'%PDF-1.4 fake contract'), save=True)
    return doc


@pytest.fixture
def company_settings(db):
    """Pre-configured company settings singleton."""
    obj, _ = CompanySettings.objects.update_or_create(
        pk=1,
        defaults={
            'contractor_full_name': 'CARLOS MARIO BLANCO PEREZ',
            'contractor_cedula': '1.037.635.428',
            'contractor_email': 'team@projectapp.co',
            'bank_name': 'Bancolombia',
            'bank_account_type': 'Ahorros',
            'bank_account_number': '26292039530',
            'contract_city': 'Medellín',
        },
    )
    return obj

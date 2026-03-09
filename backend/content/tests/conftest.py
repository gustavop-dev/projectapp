"""Shared pytest fixtures for the content app test suite.

Provides reusable fixtures for API clients, model instances,
and authenticated users following the project testing standards.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from content.models import (
    BlogPost,
    BusinessProposal,
    Category,
    Contact,
    Design,
    Hosting,
    Item,
    Model3D,
    PortfolioWork,
    Product,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
    ProposalShareLink,
)

User = get_user_model()


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
def design(db):
    """A sample design entry (without actual image files)."""
    return Design.objects.create(
        title_en='Modern Dashboard',
        title_es='Dashboard Moderno',
        category_title_en='Web Design',
        category_title_es='Diseño Web',
    )


@pytest.fixture
def model_3d(db):
    """A sample 3D model entry (without actual files)."""
    return Model3D.objects.create(
        title_en='Product Viewer',
        title_es='Visor de Producto',
        category_title_en='3D Animation',
        category_title_es='Animación 3D',
    )


@pytest.fixture
def item(db):
    """A sample item for product categories."""
    return Item.objects.create(
        name_en='Responsive Design',
        name_es='Diseño Responsivo',
    )


@pytest.fixture
def category(db, item):
    """A sample product category with one item."""
    cat = Category.objects.create(
        name_en='Web Development',
        name_es='Desarrollo Web',
    )
    cat.items.add(item)
    return cat


@pytest.fixture
def product(db, category):
    """A sample product with category (without actual image file)."""
    prod = Product.objects.create(
        title_en='E-Commerce Platform',
        title_es='Plataforma E-Commerce',
        description_en='Full e-commerce solution.',
        description_es='Solución completa de e-commerce.',
        price=Decimal('4999.99'),
        development_time_en='8-12 weeks',
        development_time_es='8-12 semanas',
    )
    prod.categories.add(category)
    return prod


@pytest.fixture
def hosting(db):
    """A sample hosting plan."""
    return Hosting.objects.create(
        title_en='Professional Plan',
        title_es='Plan Profesional',
        description_en='Best for growing businesses.',
        description_es='Ideal para negocios en crecimiento.',
        semi_annually_price=Decimal('149.99'),
        annual_price=Decimal('249.99'),
        cpu_cores_en='4 vCPUs',
        cpu_cores_es='4 vCPUs',
        ram_en='8 GB',
        ram_es='8 GB',
        storage_en='100 GB SSD',
        storage_es='100 GB SSD',
        bandwidth_en='Unlimited',
        bandwidth_es='Ilimitado',
        data_center_location_en='US East',
        data_center_location_es='Este de EE.UU.',
        operating_system_en='Ubuntu 22.04',
        operating_system_es='Ubuntu 22.04',
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
        language='es',
        total_investment=Decimal('15000.00'),
        currency='COP',
        status='draft',
        expires_at=timezone.now() + timezone.timedelta(days=30),
        reminder_days=5,
        discount_percent=20,
    )


@pytest.fixture
def sent_proposal(db):
    """A proposal that has been sent to the client."""
    return BusinessProposal.objects.create(
        title='Mobile App Development',
        client_name='Beta Inc',
        client_email='info@beta.com',
        language='en',
        total_investment=Decimal('25000.00'),
        currency='USD',
        status='sent',
        sent_at=timezone.now(),
        expires_at=timezone.now() + timezone.timedelta(days=15),
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
    return BusinessProposal.objects.create(
        title='Rejected Project',
        client_name='Declined Client',
        client_email='declined@client.com',
        language='es',
        total_investment=Decimal('8000.00'),
        currency='COP',
        status='rejected',
        rejection_reason='presupuesto alto',
        sent_at=timezone.now() - timezone.timedelta(days=5),
        expires_at=timezone.now() + timezone.timedelta(days=10),
    )


@pytest.fixture
def viewed_proposal(db):
    """A proposal that has been viewed by the client."""
    return BusinessProposal.objects.create(
        title='Viewed Project',
        client_name='Viewer Client',
        client_email='viewer@client.com',
        language='es',
        total_investment=Decimal('12000.00'),
        currency='COP',
        status='viewed',
        sent_at=timezone.now() - timezone.timedelta(days=3),
        first_viewed_at=timezone.now() - timezone.timedelta(hours=6),
        expires_at=timezone.now() + timezone.timedelta(days=20),
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

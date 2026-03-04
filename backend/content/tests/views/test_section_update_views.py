"""
Tests for proposal section update API with realistic content_json payloads.

Covers: PATCH /api/proposals/sections/:id/update/ with form-equivalent
and paste-processed data for each section type. Verifies content_json
is stored and returned correctly.
"""
import pytest
from django.urls import reverse

from content.models import BusinessProposal, ProposalSection


pytestmark = pytest.mark.django_db


@pytest.fixture
def prop(db):
    """A proposal with no sections yet."""
    return BusinessProposal.objects.create(
        title='Section Update Test',
        client_name='Test Client',
    )


def _create_section(prop, section_type, order=0):
    return ProposalSection.objects.create(
        proposal=prop,
        section_type=section_type,
        title=f'{section_type} title',
        order=order,
        content_json={},
    )


class TestUpdateGreetingSection:
    def test_saves_greeting_content_json(self, admin_client, prop):
        section = _create_section(prop, 'greeting')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'title': 'Greeting',
            'content_json': {
                'clientName': 'María García',
                'inspirationalQuote': 'Design is how it works.',
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert section.content_json['clientName'] == 'María García'
        assert section.content_json['inspirationalQuote'] == 'Design is how it works.'


class TestUpdateExecutiveSummarySection:
    def test_saves_paragraphs_and_highlights(self, admin_client, prop):
        section = _create_section(prop, 'executive_summary')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '1',
                'title': 'Resumen ejecutivo',
                'paragraphs': ['Primer párrafo.', 'Segundo párrafo.'],
                'highlightsTitle': 'Incluye',
                'highlights': ['Diseño personalizado', 'Desarrollo responsivo'],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['paragraphs']) == 2
        assert len(section.content_json['highlights']) == 2

    def test_saves_paste_processed_data(self, admin_client, prop):
        """Simulates content that was pasted and processed by the frontend."""
        section = _create_section(prop, 'executive_summary')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '1',
                'title': 'Executive Summary',
                'paragraphs': [
                    'Our proposal covers the design and development of a professional website that will serve as the primary digital presence for the business.',
                    'The solution includes responsive design, SEO optimization, and a modern technology stack.',
                ],
                'highlightsTitle': 'Includes',
                'highlights': [
                    'Custom visual design with brand alignment',
                    'Responsive web development (mobile, tablet, desktop)',
                    'Basic SEO optimization and meta tags',
                    'Contact form with email notifications',
                    'Social media integration',
                ],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['paragraphs']) == 2
        assert len(section.content_json['highlights']) == 5


class TestUpdateConversionStrategySection:
    def test_saves_steps_with_nested_bullets(self, admin_client, prop):
        section = _create_section(prop, 'conversion_strategy')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '3',
                'title': 'Estrategia de conversión',
                'intro': 'La página se construirá como herramienta de conversión.',
                'steps': [
                    {
                        'title': '👀 Captar atención',
                        'bullets': ['Mensaje claro', 'Beneficio visible', 'CTA principal'],
                    },
                    {
                        'title': '🤝 Construir confianza',
                        'bullets': ['Testimonios', 'Credenciales'],
                    },
                ],
                'resultTitle': '🎯 Resultado',
                'result': 'Una página que genere contactos reales.',
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['steps']) == 2
        assert len(section.content_json['steps'][0]['bullets']) == 3


class TestUpdateFunctionalRequirementsSection:
    def test_saves_groups_with_items_via_form(self, admin_client, prop):
        section = _create_section(prop, 'functional_requirements')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '7',
                'title': 'Requerimientos Funcionales',
                'intro': 'Detalle de requerimientos.',
                'groups': [
                    {
                        'id': 'views',
                        'icon': '🖥️',
                        'title': 'Vistas',
                        'description': 'Pantallas del sitio.',
                        'items': [
                            {'icon': '🏠', 'name': 'Página Principal', 'description': 'Landing con CTAs.'},
                            {'icon': '📧', 'name': 'Contacto', 'description': 'Formulario.'},
                            {'icon': '📜', 'name': 'Legales', 'description': 'Términos y privacidad.'},
                        ],
                    },
                    {
                        'id': 'components',
                        'icon': '🧩',
                        'title': 'Componentes',
                        'description': 'Elementos reutilizables.',
                        'items': [
                            {'icon': '🔝', 'name': 'Header', 'description': 'Logo y menú.'},
                            {'icon': '🔚', 'name': 'Footer', 'description': 'Derechos y enlaces.'},
                        ],
                    },
                ],
                'additionalModules': [],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['groups']) == 2
        assert len(section.content_json['groups'][0]['items']) == 3
        assert section.content_json['groups'][0]['items'][0]['name'] == 'Página Principal'

    def test_saves_groups_with_paste_processed_items(self, admin_client, prop):
        """Simulates items parsed from pasted text by processGroupPaste()."""
        section = _create_section(prop, 'functional_requirements')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '7',
                'title': 'Functional Requirements',
                'intro': 'Below are the project requirements.',
                'groups': [
                    {
                        'id': 'views',
                        'icon': '🖥️',
                        'title': 'Views',
                        'description': 'Each view is a screen of the website.',
                        'items': [
                            {'icon': '🏠', 'name': 'Home Page', 'description': 'Main landing page with CTAs.'},
                            {'icon': '📧', 'name': 'Contact', 'description': 'Contact form and details.'},
                            {'icon': '📜', 'name': 'Legal', 'description': 'Terms and privacy.'},
                            {'icon': '🛒', 'name': 'Products', 'description': 'Product catalog with filters.'},
                        ],
                    },
                ],
                'additionalModules': [
                    {
                        'icon': '📊',
                        'title': 'Analytics Module',
                        'description': 'Dashboard with metrics.',
                        'items': [
                            {'icon': '📈', 'name': 'Traffic Reports', 'description': 'Automatic traffic reports.'},
                            {'icon': '🎯', 'name': 'Conversion Tracking', 'description': 'Track form submissions.'},
                        ],
                    },
                ],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['groups'][0]['items']) == 4
        assert len(section.content_json['additionalModules']) == 1
        assert len(section.content_json['additionalModules'][0]['items']) == 2

    def test_saves_with_empty_items_array(self, admin_client, prop):
        section = _create_section(prop, 'functional_requirements')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '7',
                'title': 'Reqs',
                'intro': '',
                'groups': [
                    {'id': 'views', 'icon': '🖥️', 'title': 'Views', 'description': '', 'items': []},
                ],
                'additionalModules': [],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert section.content_json['groups'][0]['items'] == []


class TestUpdateTimelineSection:
    def test_saves_phases_with_tasks_array(self, admin_client, prop):
        section = _create_section(prop, 'timeline')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '8',
                'title': 'Cronograma',
                'introText': 'Fases del proyecto.',
                'totalDuration': '1 mes',
                'phases': [
                    {
                        'title': '🎨 Diseño',
                        'duration': '1 semana',
                        'description': 'Diseño visual.',
                        'tasks': ['Moodboard', 'Wireframes', 'Diseño UI'],
                        'milestone': 'Diseño aprobado',
                    },
                ],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['phases'][0]['tasks']) == 3


class TestUpdateInvestmentSection:
    def test_saves_investment_with_payment_options(self, admin_client, prop):
        section = _create_section(prop, 'investment')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '9',
                'title': 'Inversión',
                'introText': 'La inversión total es:',
                'totalInvestment': '$3.500.000',
                'currency': 'COP',
                'whatsIncluded': [
                    {'icon': '🎨', 'title': 'Diseño', 'description': 'UX/UI'},
                ],
                'paymentOptions': [
                    {'label': '40% al firmar', 'description': '$1.400.000'},
                    {'label': '30% al aprobar', 'description': '$1.050.000'},
                    {'label': '30% al desplegar', 'description': '$1.050.000'},
                ],
                'paymentMethods': ['Transferencia', 'Nequi'],
                'valueReasons': ['Diseño a medida'],
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['paymentOptions']) == 3
        assert section.content_json['totalInvestment'] == '$3.500.000'


class TestUpdateNextStepsSection:
    def test_saves_next_steps_with_ctas_and_contacts(self, admin_client, prop):
        section = _create_section(prop, 'next_steps')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'content_json': {
                'index': '11',
                'title': 'Próximos pasos',
                'introMessage': 'Estamos listos.',
                'steps': [
                    {'title': 'Revisión', 'description': 'Revisa la propuesta.'},
                    {'title': '¡Comenzamos!', 'description': 'Kickoff meeting.'},
                ],
                'ctaMessage': 'Contáctanos hoy.',
                'primaryCTA': {'text': 'WhatsApp', 'link': 'https://wa.me/123'},
                'secondaryCTA': {'text': 'Agendar', 'link': 'https://calendly.com/x'},
                'contactMethods': [
                    {'icon': '📧', 'title': 'Email', 'value': 'hi@test.co', 'link': 'mailto:hi@test.co'},
                ],
                'validityMessage': 'Válida 30 días.',
                'thankYouMessage': 'Gracias.',
            },
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert len(section.content_json['steps']) == 2
        assert section.content_json['primaryCTA']['text'] == 'WhatsApp'
        assert len(section.content_json['contactMethods']) == 1


class TestUpdateSectionEdgeCases:
    def test_saves_empty_content_json(self, admin_client, prop):
        section = _create_section(prop, 'greeting')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {'content_json': {}}
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert section.content_json == {}

    def test_updates_title_and_content_json_together(self, admin_client, prop):
        section = _create_section(prop, 'greeting')
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {
            'title': 'New Title',
            'content_json': {'clientName': 'Updated Client'},
        }
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert section.title == 'New Title'
        assert section.content_json['clientName'] == 'Updated Client'

    def test_preserves_existing_content_when_only_title_updated(self, admin_client, prop):
        section = _create_section(prop, 'greeting')
        section.content_json = {'clientName': 'Keep Me'}
        section.save()
        url = reverse('update-proposal-section', kwargs={'section_id': section.id})
        payload = {'title': 'Only Title Changed'}
        response = admin_client.patch(url, payload, format='json')
        assert response.status_code == 200
        section.refresh_from_db()
        assert section.title == 'Only Title Changed'
        assert section.content_json['clientName'] == 'Keep Me'

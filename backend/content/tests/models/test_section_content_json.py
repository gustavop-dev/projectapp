"""Tests for ProposalSection content_json storage and retrieval per section type.

Covers: all 12 section types with realistic content_json payloads,
verifying data integrity after save/reload from the database.
"""
import pytest

from content.models import BusinessProposal, ProposalSection

pytestmark = pytest.mark.django_db


@pytest.fixture
def base_proposal(db):
    """A minimal proposal for attaching sections."""
    return BusinessProposal.objects.create(
        title='Content JSON Test Proposal',
        client_name='JSON Client',
    )


class TestGreetingContentJson:
    def test_stores_and_retrieves_greeting_data(self, base_proposal):
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='greeting',
            title='Greeting',
            content_json={
                'clientName': 'María García',
                'inspirationalQuote': 'Design is how it works.',
            },
        )
        section.refresh_from_db()
        assert section.content_json['clientName'] == 'María García'
        assert section.content_json['inspirationalQuote'] == 'Design is how it works.'

    def test_stores_empty_greeting(self, base_proposal):
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='greeting',
            title='Greeting',
            content_json={'clientName': '', 'inspirationalQuote': ''},
        )
        section.refresh_from_db()
        assert section.content_json['clientName'] == ''


class TestExecutiveSummaryContentJson:
    def test_stores_paragraphs_and_highlights(self, base_proposal):
        content = {
            'index': '1',
            'title': 'Resumen ejecutivo',
            'paragraphs': [
                'Primera párrafo del resumen.',
                'Segundo párrafo con más detalle.',
            ],
            'highlightsTitle': 'Incluye',
            'highlights': [
                'Diseño visual personalizado',
                'Desarrollo web responsivo',
                'Optimización SEO básica',
            ],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='executive_summary',
            title='Executive Summary',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['paragraphs']) == 2
        assert len(section.content_json['highlights']) == 3
        assert section.content_json['index'] == '1'

    def test_stores_empty_arrays(self, base_proposal):
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='executive_summary',
            title='ES',
            content_json={'index': '', 'title': '', 'paragraphs': [], 'highlights': []},
        )
        section.refresh_from_db()
        assert section.content_json['paragraphs'] == []
        assert section.content_json['highlights'] == []


class TestContextDiagnosticContentJson:
    def test_stores_full_context_diagnostic(self, base_proposal):
        content = {
            'index': '2',
            'title': 'Contexto',
            'paragraphs': ['El cliente busca fortalecer su presencia digital.'],
            'issuesTitle': 'Desafíos',
            'issues': ['Falta de presencia digital', 'Difícil captar clientes'],
            'opportunityTitle': 'Oportunidad',
            'opportunity': 'Crear una plataforma que genere confianza.',
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='context_diagnostic',
            title='Context',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['issues']) == 2
        assert section.content_json['opportunity'] == 'Crear una plataforma que genere confianza.'


class TestConversionStrategyContentJson:
    def test_stores_steps_with_bullets(self, base_proposal):
        content = {
            'index': '3',
            'title': 'Estrategia',
            'intro': 'La página se construirá como herramienta de conversión.',
            'steps': [
                {
                    'title': '👀 Captar atención',
                    'bullets': ['Mensaje principal claro', 'Beneficio visible'],
                },
                {
                    'title': '🤝 Construir confianza',
                    'bullets': ['Sección breve "Quién soy"', 'Credibilidad'],
                },
            ],
            'resultTitle': '🎯 Resultado esperado',
            'result': 'Una página que genere contactos.',
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='conversion_strategy',
            title='Strategy',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['steps']) == 2
        assert len(section.content_json['steps'][0]['bullets']) == 2
        assert section.content_json['result'] == 'Una página que genere contactos.'


class TestDesignUxContentJson:
    def test_stores_design_ux_data(self, base_proposal):
        content = {
            'index': '4',
            'title': 'Diseño UX',
            'paragraphs': ['El desarrollo será concebido como experiencia digital.'],
            'focusTitle': 'Estructura',
            'focusItems': ['Presentación clara', 'Integración redes sociales'],
            'objectiveTitle': 'Objetivo',
            'objective': 'Inspirar confianza desde el primer momento.',
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='design_ux',
            title='Design',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['focusItems']) == 2


class TestCreativeSupportContentJson:
    def test_stores_creative_support_data(self, base_proposal):
        content = {
            'index': '5',
            'title': 'Acompañamiento',
            'paragraphs': ['El cliente contará con acompañamiento cercano.'],
            'includesTitle': 'Incluye',
            'includes': ['Sesiones de revisión', 'Apoyo en selección visual'],
            'closing': 'Cada decisión será una co-creación.',
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='creative_support',
            title='Creative',
            content_json=content,
        )
        section.refresh_from_db()
        assert section.content_json['closing'] == 'Cada decisión será una co-creación.'


class TestDevelopmentStagesContentJson:
    def test_stores_stages_with_current_flag(self, base_proposal):
        content = {
            'stages': [
                {'icon': '✉️', 'title': 'Propuesta', 'description': 'Etapa actual.', 'current': True},
                {'icon': '🎨', 'title': 'Diseño', 'description': 'Prototipo en Figma.'},
                {'icon': '💻', 'title': 'Desarrollo', 'description': 'Implementación.'},
            ],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='development_stages',
            title='Stages',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['stages']) == 3
        assert section.content_json['stages'][0]['current'] is True
        assert 'current' not in section.content_json['stages'][1]


class TestFunctionalRequirementsContentJson:
    def test_stores_groups_with_items(self, base_proposal):
        content = {
            'index': '7',
            'title': 'Requerimientos',
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
                    ],
                },
                {
                    'id': 'components',
                    'icon': '🧩',
                    'title': 'Componentes',
                    'description': 'Elementos reutilizables.',
                    'items': [
                        {'icon': '🔝', 'name': 'Header', 'description': 'Logo y menú.'},
                    ],
                },
            ],
            'additionalModules': [
                {
                    'icon': '📊',
                    'title': 'Analytics',
                    'description': 'Dashboard de métricas.',
                    'items': [
                        {'icon': '📈', 'name': 'Reports', 'description': 'Reportes automáticos.'},
                    ],
                },
            ],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='functional_requirements',
            title='Requirements',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['groups']) == 2
        assert len(section.content_json['groups'][0]['items']) == 2
        assert len(section.content_json['additionalModules']) == 1
        assert section.content_json['additionalModules'][0]['title'] == 'Analytics'

    def test_stores_empty_groups_and_modules(self, base_proposal):
        content = {
            'index': '7',
            'title': 'Reqs',
            'intro': '',
            'groups': [],
            'additionalModules': [],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='functional_requirements',
            title='Reqs',
            content_json=content,
        )
        section.refresh_from_db()
        assert section.content_json['groups'] == []
        assert section.content_json['additionalModules'] == []


class TestTimelineContentJson:
    def test_stores_phases_with_tasks(self, base_proposal):
        content = {
            'index': '8',
            'title': 'Cronograma',
            'introText': 'El proyecto se desarrollará en fases.',
            'totalDuration': 'Aproximadamente 1 mes',
            'phases': [
                {
                    'title': '🎨 Diseño',
                    'duration': '1 semana',
                    'description': 'Diseño visual en Figma.',
                    'tasks': ['Moodboard', 'Diseño UI', 'Revisiones'],
                    'milestone': 'Diseño aprobado',
                },
                {
                    'title': '💻 Desarrollo',
                    'duration': '2 semanas',
                    'description': 'Codificación nativa.',
                    'tasks': ['Frontend responsivo', 'Backend'],
                    'milestone': 'MVP funcional',
                },
            ],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='timeline',
            title='Timeline',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['phases']) == 2
        assert len(section.content_json['phases'][0]['tasks']) == 3
        assert section.content_json['totalDuration'] == 'Aproximadamente 1 mes'


class TestInvestmentContentJson:
    def test_stores_investment_with_payment_options(self, base_proposal):
        content = {
            'index': '9',
            'title': 'Inversión',
            'introText': 'La inversión total es:',
            'totalInvestment': '$3.500.000',
            'currency': 'COP',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Diseño', 'description': 'UX/UI enfocado en conversión'},
                {'icon': '⚙️', 'title': 'Desarrollo', 'description': 'Implementación completa'},
            ],
            'paymentOptions': [
                {'label': '40% al firmar ✍️', 'description': '$1.400.000 COP'},
                {'label': '30% al aprobar diseño ✅', 'description': '$1.050.000 COP'},
                {'label': '30% al desplegar 🚀', 'description': '$1.050.000 COP'},
            ],
            'paymentMethods': ['Transferencia bancaria', 'Nequi'],
            'valueReasons': ['Diseño a medida', 'Código optimizado'],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='investment',
            title='Investment',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['whatsIncluded']) == 2
        assert len(section.content_json['paymentOptions']) == 3
        assert section.content_json['totalInvestment'] == '$3.500.000'


class TestFinalNoteContentJson:
    def test_stores_final_note_with_badges(self, base_proposal):
        content = {
            'index': '10',
            'title': 'Nota Final',
            'message': 'Creemos firmemente en esta propuesta.',
            'personalNote': 'Estamos emocionados.',
            'teamName': 'Project App',
            'teamRole': 'Socio digital',
            'contactEmail': 'hello@projectapp.co',
            'commitmentBadges': [
                {'icon': '🤝', 'title': 'Compromiso', 'description': 'Dedicación completa.'},
                {'icon': '💯', 'title': 'Calidad', 'description': 'Revisiones ilimitadas.'},
            ],
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='final_note',
            title='Final Note',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['commitmentBadges']) == 2
        assert section.content_json['contactEmail'] == 'hello@projectapp.co'


class TestNextStepsContentJson:
    def test_stores_next_steps_with_ctas_and_contacts(self, base_proposal):
        content = {
            'index': '11',
            'title': 'Próximos pasos',
            'introMessage': 'Estamos listos para comenzar.',
            'steps': [
                {'title': 'Revisión', 'description': 'Revisa la propuesta.'},
                {'title': 'Confirmación', 'description': 'Agendamos reunión.'},
            ],
            'ctaMessage': 'Contáctanos hoy mismo.',
            'primaryCTA': {'text': 'WhatsApp', 'link': 'https://wa.me/123'},
            'secondaryCTA': {'text': 'Agendar', 'link': 'https://calendly.com/test'},
            'contactMethods': [
                {'icon': '📧', 'title': 'Email', 'value': 'hello@test.co', 'link': 'mailto:hello@test.co'},
                {'icon': '📱', 'title': 'WhatsApp', 'value': '+57 123', 'link': 'https://wa.me/123'},
            ],
            'validityMessage': 'Válida por 30 días.',
            'thankYouMessage': 'Gracias por la oportunidad.',
        }
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='next_steps',
            title='Next Steps',
            content_json=content,
        )
        section.refresh_from_db()
        assert len(section.content_json['steps']) == 2
        assert section.content_json['primaryCTA']['text'] == 'WhatsApp'
        assert len(section.content_json['contactMethods']) == 2
        assert section.content_json['validityMessage'] == 'Válida por 30 días.'


class TestContentJsonUpdateInPlace:
    def test_update_content_json_preserves_other_fields(self, base_proposal):
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='greeting',
            title='Greeting',
            order=0,
            content_json={'clientName': 'Old Name', 'inspirationalQuote': 'Old quote'},
        )
        section.content_json = {'clientName': 'New Name', 'inspirationalQuote': 'New quote'}
        section.save()
        section.refresh_from_db()
        assert section.content_json['clientName'] == 'New Name'
        assert section.title == 'Greeting'
        assert section.order == 0

    def test_replace_content_json_entirely(self, base_proposal):
        section = ProposalSection.objects.create(
            proposal=base_proposal,
            section_type='executive_summary',
            title='ES',
            content_json={'index': '1', 'paragraphs': ['old']},
        )
        new_content = {'index': '1', 'title': 'New', 'paragraphs': ['p1', 'p2'], 'highlights': ['h1']}
        section.content_json = new_content
        section.save()
        section.refresh_from_db()
        assert section.content_json == new_content

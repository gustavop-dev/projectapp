"""Regression fixtures for content that used to overflow / overlap.

These build proposals with adversarially long content (huge names,
notes, many specs/tiers/requirements) and assert the generator survives,
paginates, and — for the tables — repeats its header on every page the
table spans. They complement the pure-unit invariants in
test_pdf_layout_engine.py with end-to-end model-backed renders.
"""

import io
from decimal import Decimal

import pytest
from django.utils import timezone
from pypdf import PdfReader

from content.models import BusinessProposal, ProposalSection
from content.services.pdf_utils import MARGIN_B, PAGE_H, MARGIN_T, _register_fonts
from content.services.proposal_pdf_service import (
    SECTION_RENDERERS,
    ProposalPdfService,
)

LONG_WORD = 'Superllamativoextraordinariamentelargosinespaciosdeverdad'
LONG_VALUE = ('EE.UU., Brasil, Francia, Lituania, India, Alemania, Japón, '
              'Australia, Canadá, México, Argentina, Chile y Colombia')


def _make_proposal(**overrides):
    defaults = dict(
        title='Overflow Test',
        client_name='Cliente de Prueba',
        client_email='overflow@example.com',
        language='es',
        total_investment=Decimal('987654321'),
        currency='COP',
        status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=20),
    )
    defaults.update(overrides)
    return BusinessProposal.objects.create(**defaults)


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


@pytest.mark.django_db
def test_investment_extreme_content_generates():
    """8 long specs, 3 tiers with 9-digit prices, long notes/options."""
    p = _make_proposal()
    ProposalSection.objects.create(
        proposal=p, section_type='greeting', title='Saludo', order=0,
        is_enabled=True, content_json={'clientName': p.client_name},
    )
    ProposalSection.objects.create(
        proposal=p, section_type='investment', title='Inversión', order=1,
        is_enabled=True, content_json={
            'index': '1', 'title': 'Inversión',
            'introText': 'La inversión total del proyecto es:',
            'totalInvestment': '$987,654,321', 'currency': 'COP',
            'paymentOptions': [
                {'label': f'Cuota {i} con una etiqueta larguísima que '
                          f'describe condiciones {LONG_WORD}',
                 'description': f'${i}0.000.000 COP'}
                for i in range(1, 7)
            ],
            'whatsIncluded': [
                {'title': f'Entregable {i} {LONG_WORD}',
                 'description': 'Descripción extensa del entregable que '
                                'debe envolver en varias líneas ' * 2}
                for i in range(1, 5)
            ],
            'hostingPlan': {
                'title': 'Plan de Hosting Cloud Empresarial',
                'description': 'Hosting administrado incluido.',
                'hostingPercent': 15,
                'specs': [
                    {'label': f'Especificación número {i} bastante larga',
                     'value': LONG_VALUE}
                    for i in range(8)
                ],
                'billingTiers': [
                    {'frequency': 'annual', 'months': 12,
                     'discountPercent': 40, 'label': 'Anual',
                     'badge': 'Máximo descuento disponible'},
                    {'frequency': 'semiannual', 'months': 6,
                     'discountPercent': 20, 'label': 'Semestral',
                     'badge': '20% dcto'},
                    {'frequency': 'quarterly', 'months': 3,
                     'discountPercent': 10, 'label': 'Trimestral',
                     'badge': '10% dcto'},
                ],
                'coverageNote': ' '.join([LONG_WORD] * 8),
                'freeMonths': 1,
                'freeMonthNote': 'Primer mes de regalo ' * 20,
            },
            'valueReasons': ['Calidad garantizada', 'Soporte continuo'],
        },
    )
    pdf = ProposalPdfService.generate(p)
    assert pdf[:4] == b'%PDF'
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) >= 2


@pytest.mark.django_db
def test_greeting_long_name_and_quote_generates():
    p = _make_proposal(client_name='  '.join(['Corporación'] * 6))
    ProposalSection.objects.create(
        proposal=p, section_type='greeting', title='Saludo', order=0,
        is_enabled=True, content_json={
            'clientName': 'Nombre De Cliente Extremadamente Largo Que No '
                          'Cabe En Una Línea Ni En Dos 🚀',
            'inspirationalQuote': 'Una cita inspiradora larguísima. ' * 30,
        },
    )
    ProposalSection.objects.create(
        proposal=p, section_type='final_note', title='Nota', order=1,
        is_enabled=True, content_json={'title': 'Nota', 'message': 'Gracias.'},
    )
    pdf = ProposalPdfService.generate(p)
    assert pdf[:4] == b'%PDF'


def _requirements_proposal():
    p = _make_proposal()
    ProposalSection.objects.create(
        proposal=p, section_type='greeting', title='Saludo', order=0,
        is_enabled=True, content_json={'clientName': p.client_name},
    )
    ProposalSection.objects.create(
        proposal=p, section_type='functional_requirements',
        title='Requerimientos', order=1, is_enabled=True, content_json={
            'index': '1', 'title': 'Requerimientos Funcionales',
            'intro': 'Detalle completo.',
            'groups': [{
                'title': 'Vistas',
                'description': 'Pantallas del sitio.',
                'items': [
                    {'name': f'Requerimiento {i} con nombre largo',
                     'description': ('Descripción muy extensa del '
                                     'requerimiento que ocupa varias '
                                     'líneas. ' * 6)}
                    for i in range(60)
                ],
            }],
            'additionalModules': [],
        },
    )
    return p


@pytest.mark.django_db
def test_requirement_group_large_generates_and_paginates():
    """A 60-item group must render and span multiple pages without error.

    (Header-repeat across pages is asserted in test_proposal_pdf_overflow
    Fase 3 once the bespoke requirement table is migrated.)"""
    pdf = ProposalPdfService.generate(_requirements_proposal())
    assert pdf[:4] == b'%PDF'
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) >= 3


@pytest.mark.django_db
def test_all_section_renderers_stay_above_bottom_margin():
    """Every renderer, fed adversarial data, must return y >= MARGIN_B —
    a smaller y means it drew below the margin without paginating."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    p = _make_proposal()
    big_text = ' '.join([LONG_WORD] * 40)
    adversarial = {
        'index': '1', 'title': f'Título {big_text}',
        'introText': big_text, 'intro': big_text, 'message': big_text,
        'personalNote': big_text, 'paragraphs': [big_text],
        'highlights': [big_text], 'issues': [big_text],
        'opportunity': big_text, 'result': big_text,
        'focusItems': [big_text], 'objective': big_text,
        'includes': [big_text], 'closing': big_text,
        'valueReasons': [big_text],
        'steps': [{'title': big_text, 'bullets': [big_text],
                   'description': big_text}],
        'stages': [{'title': big_text, 'description': big_text,
                    'current': True}],
        'phases': [{'title': big_text, 'duration': '1 semana',
                    'description': big_text, 'tasks': [big_text],
                    'milestone': big_text}],
        'whatsIncluded': [{'title': big_text, 'description': big_text}],
        'paymentOptions': [{'label': big_text, 'description': big_text}],
        'contactMethods': [{'title': 'Email', 'value': big_text}],
        'packages': [{'name': big_text, 'hours': 10, 'note': big_text}],
        'scopeParagraphs': [big_text],
    }
    for stype, renderer in SECTION_RENDERERS.items():
        if stype == 'greeting':
            continue  # single fixed page by design
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=A4)
        ps = {'num': 3, 'client': 'Cliente', 'total': None}
        y = renderer(c, adversarial, p, ps=ps, y=PAGE_H - MARGIN_T)
        assert y >= MARGIN_B - 1, f'{stype} returned y={y} below margin'

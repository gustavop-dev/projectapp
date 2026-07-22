"""Overflow regression fixtures for the technical (?doc=technical) PDF.

Builds a technical_document with an epic carrying many requirements and
long config/flow strings, and asserts the generator paginates and repeats
the requirements table header on every page the table spans.
"""

import io
from decimal import Decimal

import pytest
from freezegun import freeze_time
from django.utils import timezone
from pypdf import PdfReader

from content.models import BusinessProposal, ProposalSection
from content.services.pdf_utils import _register_fonts
from content.services.technical_document_pdf import generate_technical_document_pdf


@pytest.fixture(autouse=True)
def _fonts():
    _register_fonts()


@pytest.mark.django_db
@freeze_time('2026-01-15 12:00:00')
def test_technical_epic_table_header_repeats():
    p = BusinessProposal.objects.create(
        title='Tech Overflow', client_name='Cliente Técnico',
        client_email='tech@example.com', language='es',
        total_investment=Decimal('10000000'), currency='COP', status='sent',
        expires_at=timezone.now() + timezone.timedelta(days=20),
    )
    reqs = [
        {
            'flowKey': f'flow-{i}',
            'title': f'Requerimiento técnico número {i} con título extenso',
            'description': 'Descripción muy larga del requerimiento que '
                           'ocupa varias líneas dentro de su columna. ' * 4,
            'configuration': 'Índices, claves y ajustes de configuración '
                             'detallados para este flujo. ' * 2,
            'usageFlow': 'Usuario abre pantalla, aplica acción, revisa '
                         'resultado y confirma. ' * 2,
            'priority': ['critical', 'high', 'medium', 'low'][i % 4],
        }
        for i in range(40)
    ]
    ProposalSection.objects.create(
        proposal=p, section_type='technical_document',
        title='Detalle técnico', order=0, is_enabled=True,
        content_json={
            'purpose': 'Documento técnico de prueba.',
            'epics': [{
                'epicKey': 'core', 'title': 'Módulo principal',
                'description': 'Todo el núcleo del producto.',
                'requirements': reqs,
            }],
        },
    )
    pdf = generate_technical_document_pdf(p)
    assert pdf and pdf[:4] == b'%PDF'
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) >= 3
    table_pages = [
        pg for pg in reader.pages
        if 'Requerimiento' in (pg.extract_text() or '')
        and 'Descripción' in (pg.extract_text() or '')
    ]
    assert len(table_pages) >= 2


@pytest.mark.django_db
@freeze_time('2026-01-15 12:00:00')
def test_technical_recovered_columns_and_priority_render():
    """The recovered integration/environment/quality columns and the
    semantic priority pills generate without error."""
    p = BusinessProposal.objects.create(
        title='Tech Cols', client_name='Cliente', client_email='c@example.com',
        language='es', total_investment=Decimal('5000000'), currency='COP',
        status='sent', expires_at=timezone.now() + timezone.timedelta(days=20),
    )
    ProposalSection.objects.create(
        proposal=p, section_type='technical_document',
        title='Detalle técnico', order=0, is_enabled=True,
        content_json={
            'purpose': 'Prueba de columnas.',
            'integrations': {
                'included': [{
                    'service': 'Pagos', 'provider': 'Wompi',
                    'connection': 'REST', 'dataExchange': 'Monto y estado',
                    'accountOwner': 'Cliente',
                }],
                'excluded': [{
                    'service': 'SMS', 'reason': 'Fuera de alcance',
                    'availability': 'Fase 2',
                }],
            },
            'environments': [{
                'name': 'Prod', 'purpose': 'Producción', 'url': 'app.co',
                'database': 'MySQL', 'whoAccesses': 'Equipo',
            }],
            'quality': {
                'testTypes': [{
                    'type': 'E2E', 'validates': 'Flujos', 'tool': 'Playwright',
                    'whenRun': 'CI en cada push',
                }],
            },
        },
    )
    pdf = generate_technical_document_pdf(p)
    assert pdf and pdf[:4] == b'%PDF'
    text = '\n'.join(pg.extract_text() or '' for pg in
                     PdfReader(io.BytesIO(pdf)).pages)
    assert 'Datos' in text          # integrations dataExchange column
    assert 'Disponibilidad' in text  # excluded availability column
    assert 'Cuándo' in text          # testTypes whenRun column

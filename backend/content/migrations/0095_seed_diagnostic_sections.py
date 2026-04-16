"""Data migration: backfill DiagnosticSection rows for existing diagnostics.

Every WebAppDiagnostic that was created before the JSON-section refactor
receives the default 8 sections from ``content.seeds.diagnostic_template``.
No content is preserved from the legacy ``DiagnosticDocument.content_md``
because that content was the same for every diagnostic (a fresh copy of the
markdown template) — the admin re-authors findings directly on the JSON
sections now.
"""

from django.db import migrations


def _seed_specs():
    # Inline lightweight copy of content.seeds.diagnostic_template.default_sections()
    # to keep the migration independent from app code that may change later.
    return [
        {
            'section_type': 'purpose',
            'title': 'Propósito',
            'order': 1,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '1',
                'title': 'Propósito',
                'paragraphs': [],
                'severityTitle': 'Escala de Severidad',
                'severityLevels': [],
            },
        },
        {
            'section_type': 'radiography',
            'title': 'Radiografía de la Aplicación',
            'order': 2,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '2',
                'title': 'Radiografía de la Aplicación',
                'intro': '',
                'includes': [],
                'classificationRows': [],
            },
        },
        {
            'section_type': 'categories',
            'title': 'Categorías Evaluadas',
            'order': 3,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '3',
                'title': 'Categorías que se evalúan en el diagnóstico',
                'intro': '',
                'categories': [],
            },
        },
        {
            'section_type': 'delivery_structure',
            'title': 'Estructura de la Entrega',
            'order': 4,
            'visibility': 'initial',
            'is_enabled': True,
            'content_json': {
                'index': '4',
                'title': 'Estructura de la Entrega',
                'intro': '',
                'blocks': [],
            },
        },
        {
            'section_type': 'executive_summary',
            'title': 'Resumen Ejecutivo',
            'order': 5,
            'visibility': 'final',
            'is_enabled': True,
            'content_json': {
                'index': '5',
                'title': 'Resumen Ejecutivo',
                'intro': '',
                'severityCounts': {
                    'critico': 0, 'alto': 0, 'medio': 0, 'bajo': 0,
                },
                'narrative': '',
                'highlights': [],
            },
        },
        {
            'section_type': 'cost',
            'title': 'Costo y Formas de Pago',
            'order': 6,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '6',
                'title': 'Costo y Formas de Pago',
                'intro': '',
                'paymentDescription': [],
                'note': '',
            },
        },
        {
            'section_type': 'timeline',
            'title': 'Cronograma',
            'order': 7,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '7',
                'title': 'Cronograma',
                'intro': '',
                'distributionTitle': 'Distribución general',
                'distribution': [],
            },
        },
        {
            'section_type': 'scope',
            'title': 'Alcance y Consideraciones',
            'order': 8,
            'visibility': 'both',
            'is_enabled': True,
            'content_json': {
                'index': '8',
                'title': 'Alcance y Consideraciones',
                'considerations': [],
            },
        },
    ]


def seed_existing_diagnostics(apps, schema_editor):
    WebAppDiagnostic = apps.get_model('content', 'WebAppDiagnostic')
    DiagnosticSection = apps.get_model('content', 'DiagnosticSection')
    try:
        from content.seeds.diagnostic_template import default_sections
        specs = default_sections()
    except Exception:
        specs = _seed_specs()

    for diagnostic in WebAppDiagnostic.objects.all():
        existing_types = set(
            diagnostic.sections.values_list('section_type', flat=True)
        )
        for spec in specs:
            if spec['section_type'] in existing_types:
                continue
            DiagnosticSection.objects.create(
                diagnostic=diagnostic,
                section_type=spec['section_type'],
                title=spec['title'],
                order=spec['order'],
                is_enabled=spec['is_enabled'],
                visibility=spec['visibility'],
                content_json=spec['content_json'],
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0094_diagnostic_sections'),
    ]

    operations = [
        migrations.RunPython(seed_existing_diagnostics, noop_reverse),
    ]

"""Seed fake documents distributed across the nested folder tree.

Designed to make manual QA and Playwright runs realistic without setup. Assumes
`create_fake_document_folders` ran first; falls back gracefully if folders are
missing.

Run with::

    python manage.py create_fake_documents [--count N]

Idempotent: if any document with the seeded titles already exists, it's skipped.
"""
import random

from django.core.management.base import BaseCommand

from content.models import Document, DocumentFolder


# Each entry: (folder_path_segments, title, lang, status, cover_type, markdown_seed)
# folder_path_segments is a tuple of names traversed from root; () means root.
SEED_DOCS = [
    # Root-level "Clientes" docs
    (('Clientes',), 'Resumen general de clientes 2026', 'es', 'published', 'generic', 'overview'),
    (('Clientes',), 'Manual de relacionamiento comercial', 'es', 'draft', 'generic', 'manual'),
    (('Clientes',), 'Cliente onboarding checklist', 'en', 'published', 'generic', 'checklist'),

    # Deep in "Clientes / Activos / 2026 / Contratos"
    (('Clientes', 'Activos', '2026', 'Contratos'), 'Contrato Pañal S.A.S.', 'es', 'published', 'generic', 'contract'),
    (('Clientes', 'Activos', '2026', 'Contratos'), 'Contrato — Albunmanía', 'es', 'draft', 'generic', 'contract'),
    (('Clientes', 'Activos', '2026', 'Contratos'), 'NDA — Solutia Group', 'es', 'published', 'none', 'nda'),
    (('Clientes', 'Activos', '2026', 'Contratos'), 'Service Agreement — Acme Inc.', 'en', 'archived', 'generic', 'contract'),
    (('Clientes', 'Activos', '2026', 'Contratos'), 'Amendment #2 — Pañal S.A.S.', 'es', 'draft', 'generic', 'amendment'),

    # In "Activos / Pendientes de firma"
    (('Clientes', 'Activos', 'Pendientes de firma'), 'Borrador acuerdo de confidencialidad', 'es', 'draft', 'generic', 'nda'),
    (('Clientes', 'Activos', 'Pendientes de firma'), 'Pending: Master Service Agreement', 'en', 'draft', 'generic', 'msa'),

    # In "Internos / Plantillas"
    (('Internos', 'Plantillas'), 'Plantilla — Carta de bienvenida', 'es', 'published', 'generic', 'template'),
    (('Internos', 'Plantillas'), 'Plantilla — Factura de cobro', 'es', 'published', 'generic', 'invoice'),
    (('Internos', 'Plantillas'), 'Template — Onboarding email', 'en', 'published', 'generic', 'email'),

    # In "Internos / Recursos legales / NDAs"
    (('Internos', 'Recursos legales', 'NDAs'), 'NDA estándar — v3.2', 'es', 'published', 'none', 'nda'),
    (('Internos', 'Recursos legales', 'NDAs'), 'Mutual NDA — v1.0 (EN)', 'en', 'published', 'none', 'nda'),

    # Root-only (no folder) — exercises ?folder=none
    ((), 'Documento sin clasificar #1', 'es', 'draft', 'generic', 'misc'),
    ((), 'Notas rápidas sin clasificar', 'es', 'draft', 'none', 'notes'),
    ((), 'Untitled scratchpad', 'en', 'draft', 'none', 'misc'),

    # Edge cases
    ((), '', 'es', 'draft', 'generic', 'empty'),  # title=empty fallback handled by model? no — title required; we'll skip this one (left for edge-case extension)
    ((), 'A' * 250, 'es', 'draft', 'generic', 'long'),  # near max-length 255
    (('Clientes',), 'Cobranza 💰 — Acción requerida', 'es', 'published', 'generic', 'unicode'),  # emoji + accents
]


MARKDOWN_TEMPLATES = {
    'overview': (
        '# Resumen general\n\nEste documento presenta los **clientes** activos del periodo.\n\n'
        '## Objetivos\n\n- Consolidar relaciones existentes\n- Identificar oportunidades de upsell\n'
        '- Cerrar contratos pendientes\n\nVer detalle por carpeta.'
    ),
    'manual': (
        '# Manual de relacionamiento\n\n## Princpios\n\n1. Empatía primero\n2. Claridad sobre cortesía\n'
        '3. Documentar cada interacción\n\n## Tonos de comunicación\n\nFormal por escrito; cercano en llamadas.'
    ),
    'checklist': (
        '# Onboarding checklist\n\n- [ ] Send welcome email\n- [ ] Schedule kickoff call\n'
        '- [ ] Share NDA\n- [ ] Provision access\n- [ ] Confirm payment method'
    ),
    'contract': (
        '# Contrato de prestación de servicios\n\n## Partes\n\nEntre **El Contratante** y **El Contratista**...\n\n'
        '## Objeto\n\nDesarrollo de software a la medida.\n\n## Vigencia\n\n6 meses prorrogables.'
    ),
    'nda': (
        '# Acuerdo de Confidencialidad\n\n## Cláusula 1 — Definición\n\nSe entiende por *Información Confidencial* toda información...\n\n'
        '## Cláusula 2 — Obligaciones\n\nLa parte receptora se obliga a:\n\n- Mantener la información en secreto\n- Limitar el acceso\n- Devolver al finalizar'
    ),
    'amendment': (
        '# Otrosí #2\n\nLas partes acuerdan modificar el contrato original en los siguientes términos:\n\n'
        '1. Se extiende la vigencia hasta el 31 de diciembre de 2026.\n2. Se ajusta el valor por inflación.'
    ),
    'msa': (
        '# Master Service Agreement\n\n## Scope\n\nThis agreement governs all Statements of Work entered into between the parties.\n\n'
        '## Term\n\nInitial term of 12 months, auto-renewing annually.'
    ),
    'template': (
        '# Plantilla — Carta de bienvenida\n\nEstimado/a `{{client_name}}`,\n\nBienvenido/a a nuestra red de clientes. Estamos comprometidos con...\n\n'
        'Atentamente,\nEl equipo'
    ),
    'invoice': (
        '# Factura de cobro\n\n**Cliente:** `{{client_name}}`\n**Concepto:** Servicios profesionales\n**Total:** `{{total}}` COP\n\n'
        '## Condiciones\n\nPago a 15 días calendario.'
    ),
    'email': (
        '# Onboarding email\n\nHi `{{client_name}}`,\n\nWelcome aboard! Here\'s what to expect in your first week:\n\n'
        '1. Kickoff call (Day 1)\n2. Discovery workshop (Day 3)\n3. First deliverable (Day 7)'
    ),
    'notes': (
        '# Notas rápidas\n\n- Llamar al cliente mañana\n- Revisar propuesta enviada el 14/05\n- Confirmar fecha de demo'
    ),
    'misc': (
        '# Documento\n\nContenido pendiente de redacción.'
    ),
    'long': (
        '# Documento extenso\n\n' + ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 10)
    ),
    'empty': '',
    'unicode': (
        '# Cobranza 💰\n\nEste cliente requiere **acción inmediata** — ¿ya se contactó?\n\n'
        '## Detalles\n\n- Monto: $5.000.000 COP\n- Días vencido: 45\n- Último contacto: 2026-05-01'
    ),
}


def _resolve_folder(segments):
    """Walk the folder tree by name segments and return the leaf folder (or None)."""
    if not segments:
        return None
    parent = None
    folder = None
    for name in segments:
        folder = DocumentFolder.objects.filter(name=name, parent=parent).first()
        if folder is None:
            return None  # path missing — skip this doc
        parent = folder
    return folder


class Command(BaseCommand):
    help = 'Seed fake documents distributed across the nested folder tree.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=None,
            help='Optional cap on number of documents to create (default: all SEED_DOCS).',
        )

    def handle(self, *args, **options):
        cap = options.get('count')
        specs = SEED_DOCS if cap is None else SEED_DOCS[:cap]

        created = 0
        skipped = 0
        for segments, title, lang, status, cover, mk_seed in specs:
            if not title:
                # Empty title would fail the model — skip the edge-case entry.
                skipped += 1
                continue
            folder = _resolve_folder(segments)
            # Idempotency: skip if a document with this title + folder already exists.
            if Document.objects.filter(title=title, folder=folder).exists():
                skipped += 1
                continue
            Document.objects.create(
                title=title,
                folder=folder,
                content_markdown=MARKDOWN_TEMPLATES.get(mk_seed, ''),
                status=status,
                language=lang,
                cover_type=cover,
            )
            created += 1

        total = Document.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'{created} document(s) created, {skipped} skipped (total in DB: {total}).'
            )
        )

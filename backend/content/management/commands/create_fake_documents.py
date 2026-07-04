"""Management command — create fake Document graph for local / demo use.

Builds the full commercial documents feature with business sense:

* one ``IssuerProfile`` (legal entity),
* a **hierarchical** ``DocumentFolder`` tree (exercises the folder/parent feature),
* a palette of ``DocumentTag`` labels,
* ``Document`` records split between markdown notes and collection accounts,
  each collection account carrying coherent ``DocumentItem`` lines (whose totals
  add up), a ``DocumentCollectionAccount`` 1:1 extension and ``DocumentPaymentMethod``.

Collection accounts are pushed through their real lifecycle
(draft → issued → paid / cancelled / overdue) via ``collection_account_service``
so ``public_number`` is allocated exactly like in production.

Idempotent: re-running skips creation if fake documents already exist.
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Project, UserProfile
from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentFolder,
    DocumentItem,
    DocumentPaymentMethod,
    DocumentTag,
    DocumentType,
)
from content.services import collection_account_service as ca_service
from content.services.document_type_codes import COLLECTION_ACCOUNT, MARKDOWN

User = get_user_model()


# ── Static pools ──────────────────────────────────────────────────────────

FOLDER_TREE = [
    ('Comercial', [
        ('2026', [
            ('Cuentas de cobro', []),
            ('Facturas', []),
        ]),
        ('Contratos', []),
    ]),
    ('Documentación', [
        ('Manuales', []),
        ('Anexos', []),
    ]),
]

TAGS = [
    ('Urgente', DocumentTag.Color.RED),
    ('Pagado', DocumentTag.Color.EMERALD),
    ('Pendiente', DocumentTag.Color.YELLOW),
    ('Cliente VIP', DocumentTag.Color.PURPLE),
    ('Interno', DocumentTag.Color.GRAY),
    ('Revisar', DocumentTag.Color.BLUE),
]

BILLING_CONCEPTS = [
    'Desarrollo de plataforma web — Fase 1',
    'Anticipo de proyecto (40%)',
    'Saldo final de proyecto (30%)',
    'Mensualidad de hosting y mantenimiento',
    'Soporte técnico y ajustes funcionales',
    'Diseño UX/UI e identidad visual',
    'Integración de pasarela de pagos',
    'Migración y puesta en producción',
]

MARKDOWN_DOCS = [
    ('Manual de uso del panel de administración',
     '# Manual del panel\n\nGuía rápida para gestionar propuestas, clientes y documentos.\n\n## Acceso\nIngrese con su usuario de administrador.\n'),
    ('Acta de inicio de proyecto',
     '# Acta de inicio\n\nSe deja constancia del arranque del proyecto, alcance y entregables acordados.\n'),
    ('Política de tratamiento de datos',
     '# Tratamiento de datos\n\nDescribe cómo se recolectan, usan y protegen los datos personales.\n'),
    ('Guía de marca y lineamientos visuales',
     '# Guía de marca\n\nColores, tipografías y uso del logotipo para piezas digitales.\n'),
    ('Anexo técnico — arquitectura de la solución',
     '# Anexo técnico\n\nStack: Django + Nuxt + MySQL. Describe módulos, integraciones y despliegue.\n'),
    ('Checklist de entrega y aceptación',
     '# Checklist de entrega\n\n- [ ] Pruebas de aceptación\n- [ ] Capacitación\n- [ ] Puesta en producción\n'),
]

ITEM_TEMPLATES = [
    (DocumentItem.ItemType.SERVICE, 'Desarrollo a medida — módulo funcional'),
    (DocumentItem.ItemType.ADVANCE, 'Anticipo del proyecto (40%)'),
    (DocumentItem.ItemType.BALANCE, 'Saldo final del proyecto (30%)'),
    (DocumentItem.ItemType.HOSTING, 'Hosting y mantenimiento mensual'),
    (DocumentItem.ItemType.SUPPORT, 'Soporte técnico y ajustes'),
]


def _ensure_issuer():
    from content.models import IssuerProfile

    issuer, _ = IssuerProfile.objects.get_or_create(
        name='ProjectApp',
        defaults={
            'legal_name': 'ProjectApp S.A.S.',
            'identification_type': 'NIT',
            'identification_number': '901.234.567-8',
            'email': 'facturacion@projectapp.dev',
            'phone': '+57 300 123 4567',
            'address': 'Calle 123 #45-67',
            'city': 'Bogotá',
            'country': 'CO',
            'public_number_prefix': 'PA',
        },
    )
    return issuer


def _ensure_folders():
    """Create the folder tree, return a flat list of leaf folders."""
    leaves = []

    def walk(specs, parent):
        for name, children in specs:
            folder, _ = DocumentFolder.objects.get_or_create(
                name=name, parent=parent,
                defaults={'order': 0},
            )
            if children:
                walk(children, folder)
            else:
                leaves.append(folder)

    walk(FOLDER_TREE, None)
    return leaves


def _ensure_tags():
    tags = []
    for name, color in TAGS:
        tag, _ = DocumentTag.objects.get_or_create(name=name, defaults={'color': color})
        tags.append(tag)
    return tags


def _doc_type(code, name):
    dt, _ = DocumentType.objects.get_or_create(code=code, defaults={'name': name})
    return dt


def _client_candidates():
    """Return (project, client_user) pairs usable for collection accounts."""
    pairs = []
    for project in Project.objects.select_related('client').all():
        if project.client_id:
            pairs.append((project, project.client))
    # Fallback: standalone client users (no project) so we still have customers.
    for profile in UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT).select_related('user'):
        pairs.append((None, profile.user))
    return pairs


class Command(BaseCommand):
    help = 'Create a fake Document graph (issuer, folders, tags, markdown + collection accounts).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=40,
            help='Total number of Document records to create (default: 40).',
        )

    def handle(self, *args, **options):
        count = max(1, options['count'])

        if Document.objects.count() >= count:
            self.stdout.write(self.style.WARNING(
                f'{Document.objects.count()} documents already exist — skipped. '
                'Run delete_fake_data --confirm first to regenerate.'
            ))
            return

        rng = random.Random(7)
        admin = User.objects.filter(is_staff=True).first()
        issuer = _ensure_issuer()
        leaves = _ensure_folders()
        tags = _ensure_tags()
        md_type = _doc_type(MARKDOWN, 'Documento markdown')
        ca_type = _doc_type(COLLECTION_ACCOUNT, 'Cuenta de cobro')
        clients = _client_candidates()

        if not clients:
            self.stdout.write(self.style.WARNING(
                'No client users/projects found — collection accounts will stay as drafts. '
                'Run seed_platform_data first for richer data.'
            ))

        n_markdown = count // 2
        n_collection = count - n_markdown
        created_md = 0
        created_ca = 0

        # ── Markdown documents ────────────────────────────────────────────
        md_folders = [f for f in leaves if f.name in ('Manuales', 'Anexos')] or leaves
        for i in range(n_markdown):
            title_base, body = MARKDOWN_DOCS[i % len(MARKDOWN_DOCS)]
            cycle = i // len(MARKDOWN_DOCS)
            title = f'{title_base}{" v" + str(cycle + 1) if cycle else ""}'
            status = rng.choices(
                [Document.Status.PUBLISHED, Document.Status.DRAFT, Document.Status.ARCHIVED],
                weights=[6, 3, 1],
            )[0]
            doc = Document.objects.create(
                document_type=md_type,
                folder=rng.choice(md_folders),
                title=title,
                status=status,
                content_markdown=body,
                language=Document.Language.ES,
                created_by=admin,
                updated_by=admin,
            )
            doc.tags.add(*rng.sample(tags, k=rng.randint(1, 2)))
            created_md += 1

        # ── Collection accounts ───────────────────────────────────────────
        ca_folders = [f for f in leaves if f.name in ('Cuentas de cobro', 'Facturas')] or leaves
        # Lifecycle buckets across the generated accounts.
        lifecycles = self._lifecycle_plan(n_collection)

        for i in range(n_collection):
            lifecycle = lifecycles[i]
            project, client_user = (rng.choice(clients) if clients else (None, None))
            concept = BILLING_CONCEPTS[i % len(BILLING_CONCEPTS)]
            currency = 'COP'

            doc = Document.objects.create(
                document_type=ca_type,
                folder=rng.choice(ca_folders),
                title=f'Cuenta de cobro — {concept}',
                status=Document.Status.PUBLISHED,
                commercial_status=Document.CommercialStatus.DRAFT,
                language=Document.Language.ES,
                city='Bogotá',
                currency=currency,
                project=project,
                client_user=client_user,
                client_name=(getattr(client_user, 'get_full_name', lambda: '')() or '') if client_user else '',
                created_by=admin,
                updated_by=admin,
                notes='Generado para demo local.',
                terms_and_conditions='Pago dentro del plazo indicado. Valores en pesos colombianos.',
            )
            doc.tags.add(*rng.sample(tags, k=rng.randint(1, 2)))

            # Collection account extension with payment term.
            term_days = rng.choice([8, 15, 30])
            ext = DocumentCollectionAccount.objects.create(
                document=doc,
                billing_concept=concept,
                payment_term_type=DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE,
                payment_term_days=term_days,
            )

            self._add_items(doc, rng, currency)
            self._add_payment_method(doc, issuer)
            ca_service.recalculate_document_totals(doc)
            doc.save(update_fields=['subtotal', 'tax_total', 'total', 'updated_at'])

            self._apply_lifecycle(doc, ext, issuer, admin, lifecycle, rng)
            created_ca += 1

        # ── Client-portal signable contracts (unsigned + signed) ─────────────
        self._create_signable_documents(admin, md_type, leaves)

        self.stdout.write(self.style.SUCCESS(
            f'Documents created: {created_md} markdown + {created_ca} collection accounts. '
            f'Issuer "{issuer.name}", {len(leaves)} leaf folders, {len(tags)} tags.'
        ))

    # ── helpers ────────────────────────────────────────────────────────────

    # Repeating cycle with business-realistic weights: ~1 draft, 4 issued,
    # 6 paid, 2 overdue, 1 cancelled per 14 accounts.
    _LIFECYCLE_CYCLE = (
        ['draft'] + ['issued'] * 4 + ['paid'] * 6 + ['overdue'] * 2 + ['cancelled']
    )

    def _lifecycle_plan(self, n):
        """Spread accounts across lifecycle states with business-realistic weights."""
        cycle = self._LIFECYCLE_CYCLE
        return [cycle[i % len(cycle)] for i in range(n)]

    def _add_items(self, doc, rng, currency):
        n_lines = rng.randint(1, 3)
        for position in range(n_lines):
            item_type, desc = ITEM_TEMPLATES[position % len(ITEM_TEMPLATES)]
            quantity = Decimal('1')
            base = rng.choice([350000, 500000, 750000, 1200000, 2500000]) if currency == 'COP' \
                else rng.choice([300, 500, 800, 1200])
            unit_price = Decimal(str(base))
            discount = Decimal('0')
            taxable = quantity * unit_price - discount
            tax = (taxable * Decimal('0.19')).quantize(Decimal('0.01'))  # IVA 19%
            line_total = taxable + tax
            DocumentItem.objects.create(
                document=doc,
                position=position,
                item_type=item_type,
                description=desc,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount,
                tax_amount=tax,
                line_total=line_total,
            )

    def _add_payment_method(self, doc, issuer):
        DocumentPaymentMethod.objects.create(
            document=doc,
            payment_method_type=DocumentPaymentMethod.MethodType.BANK_TRANSFER,
            bank_name='Bancolombia',
            account_type='Ahorros',
            account_number='123-456789-00',
            account_holder_name=issuer.legal_name or issuer.name,
            account_holder_identification=issuer.identification_number,
            payment_instructions='Enviar comprobante a facturacion@projectapp.dev',
            is_primary=True,
        )

    def _apply_lifecycle(self, doc, ext, issuer, admin, lifecycle, rng):
        """Move a draft collection account into its target lifecycle state."""
        can_issue = bool(doc.client_user_id or (doc.project_id and doc.project.client_id))
        if lifecycle == 'draft' or not can_issue:
            return

        if lifecycle == 'overdue':
            # Past fixed due date so the derived "overdue" flag turns on.
            ext.payment_term_type = DocumentCollectionAccount.PaymentTermType.FIXED_DATE
            ext.save(update_fields=['payment_term_type'])
            doc.due_date = timezone.now().date() - timedelta(days=rng.randint(5, 40))
            doc.save(update_fields=['due_date', 'updated_at'])

        try:
            ca_service.issue_collection_account(doc, issuer=issuer, acting_user=admin)
        except ca_service.CollectionAccountError:
            return

        if lifecycle == 'paid':
            ca_service.mark_collection_account_paid(doc, acting_user=admin)
        elif lifecycle == 'cancelled':
            ca_service.mark_collection_account_cancelled(doc, acting_user=admin)

    def _create_signable_documents(self, admin, md_type, leaves):
        """Create one unsigned + one signed contract for a project-backed client.

        Exercises the client-portal signature flow (/platform/documents): a
        published, signature-required contract the client must accept, plus an
        already-signed sibling carrying the acceptance stamp. Idempotent — guarded
        by (title, project, requires_signature) so re-runs never duplicate.
        """
        project = (
            Project.objects.filter(client__isnull=False)
            .select_related('client')
            .order_by('id')
            .first()
        )
        if not project or not project.client_id:
            self.stdout.write(self.style.WARNING(
                '  No project-backed client found — skipping signable documents. '
                'Run seed_platform_data first.'
            ))
            return

        client_user = project.client
        client_full_name = (
            (getattr(client_user, 'get_full_name', lambda: '')() or '').strip()
            or client_user.email
        )
        contract_folder = (
            next((f for f in leaves if f.name == 'Contratos'), None)
            or (leaves[0] if leaves else None)
        )

        created = 0

        # Unsigned, signature-required contract (client must sign in the portal).
        unsigned_title = 'Contrato de servicios'
        if not Document.objects.filter(
            title=unsigned_title, project=project, requires_signature=True,
        ).exists():
            Document.objects.create(
                document_type=md_type,
                folder=contract_folder,
                title=unsigned_title,
                status=Document.Status.PUBLISHED,
                language=Document.Language.ES,
                content_markdown=(
                    '# Contrato de servicios\n\n'
                    'Contrato de prestación de servicios de desarrollo web. '
                    'Por favor revise y firme para dar inicio al proyecto.\n'
                ),
                project=project,
                client_user=client_user,
                client_name=client_full_name,
                requires_signature=True,
                created_by=admin,
                updated_by=admin,
            )
            created += 1

        # Already-signed contract (acceptance stamp filled in).
        signed_title = 'Contrato de servicios firmado'
        if not Document.objects.filter(
            title=signed_title, project=project, requires_signature=True,
        ).exists():
            Document.objects.create(
                document_type=md_type,
                folder=contract_folder,
                title=signed_title,
                status=Document.Status.PUBLISHED,
                language=Document.Language.ES,
                content_markdown=(
                    '# Contrato de servicios\n\n'
                    'Contrato de prestación de servicios de desarrollo web '
                    '(aceptado por el cliente).\n'
                ),
                project=project,
                client_user=client_user,
                client_name=client_full_name,
                requires_signature=True,
                signed_at=timezone.now(),
                signed_by=client_user,
                signature_name=client_full_name,
                signature_ip='127.0.0.1',
                signature_user_agent='Mozilla/5.0 (fake-data)',
                created_by=admin,
                updated_by=admin,
            )
            created += 1

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'  Signable documents created: {created} '
                f'(client "{client_full_name}", project "{project.name}").'
            ))
        else:
            self.stdout.write('  Signable documents already present — skipped.')

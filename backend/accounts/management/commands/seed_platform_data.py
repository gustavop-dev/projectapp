"""
Seed the platform with demo data for development.

Creates:
  - 1 admin user (admin@projectapp.dev / Admin1234!)
  - 1 onboarded client (maria@techstartup.co / Client1234!)
  - 1 full demo BusinessProposal (all default sections + populated technical_document) for TechStartup
  - 2 demo projects for the client
  - Kanban, change requests, bugs, deliverables, hosting + extra payments (pending / overdue / failed)
  - Collection accounts (titles prefixed [Demo]) for platform QA
  - In-app notifications + requirement/bug comments (titles/content prefixed [Seed])
  - Markdown panel documents (titles prefixed [Seed]) for PDF pipeline tests

Usage:
  python manage.py seed_platform_data
  python manage.py seed_platform_data --flush   # removes previous seed data first
"""

import os
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from accounts.models import (
    BugComment,
    BugReport,
    ChangeRequest,
    ChangeRequestComment,
    Deliverable,
    HostingSubscription,
    Notification,
    Payment,
    Project,
    Requirement,
    RequirementComment,
    UserProfile,
)

User = get_user_model()

ADMIN_EMAIL = 'admin@projectapp.dev'
CLIENT_EMAIL = 'maria@techstartup.co'

# Synthetic notifications / markdown docs; removed on --flush.
SEED_PREFIX = '[Seed]'

ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', 'Admin1234!')
CLIENT_PASSWORD = os.environ.get('SEED_CLIENT_PASSWORD', 'Client1234!')


class Command(BaseCommand):
    help = 'Seed platform with one admin and one onboarded client for development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Remove existing seed users before creating new ones.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        admin_user = self._create_admin()
        client_user = self._create_client(created_by=admin_user)
        self._create_projects(client_user, admin_user)

        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully:'))
        self.stdout.write(f'  Admin  → {ADMIN_EMAIL} / (env SEED_ADMIN_PASSWORD or Admin1234!)')
        self.stdout.write(f'  Client → {CLIENT_EMAIL} / (env SEED_CLIENT_PASSWORD or Client1234!)')
        self.stdout.write('')

    def _flush(self):
        from content.models import Document
        from content.services.document_type_codes import COLLECTION_ACCOUNT

        seed_docs = Document.objects.filter(title__startswith=SEED_PREFIX).delete()
        if seed_docs[0]:
            self.stdout.write(f'  Deleted {seed_docs[0]} documents titled {SEED_PREFIX!r}')

        n_del, _ = Notification.objects.filter(title__startswith=SEED_PREFIX).delete()
        if n_del:
            self.stdout.write(f'  Deleted {n_del} seed-titled notifications')

        for email in [ADMIN_EMAIL, CLIENT_EMAIL]:
            user = User.objects.filter(email=email).first()
            if user:
                Document.objects.filter(document_type__code=COLLECTION_ACCOUNT).filter(
                    Q(project__client=user) | Q(client_user=user),
                ).delete()
                Project.objects.filter(client=user).delete()
                user.delete()
                self.stdout.write(f'  Deleted existing user: {email}')

    def _create_admin(self):
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            self.stdout.write(f'  Admin already exists: {ADMIN_EMAIL}')
            return User.objects.get(email=ADMIN_EMAIL)

        user = User.objects.create_user(
            username=ADMIN_EMAIL,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name='Gustavo',
            last_name='Pérez',
            is_staff=True,
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_ADMIN,
            is_onboarded=True,
            profile_completed=True,
            company_name='ProjectApp',
            phone='+57 310 555 0001',
        )
        self.stdout.write(self.style.SUCCESS(f'  Created admin: {ADMIN_EMAIL}'))
        return user

    def _create_client(self, created_by=None):
        if User.objects.filter(email=CLIENT_EMAIL).exists():
            self.stdout.write(f'  Client already exists: {CLIENT_EMAIL}')
            return User.objects.get(email=CLIENT_EMAIL)

        user = User.objects.create_user(
            username=CLIENT_EMAIL,
            email=CLIENT_EMAIL,
            password=CLIENT_PASSWORD,
            first_name='María',
            last_name='Torres',
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_CLIENT,
            is_onboarded=True,
            profile_completed=True,
            company_name='TechStartup Co.',
            phone='+57 300 123 4567',
            cedula='1020304050',
            date_of_birth='1992-06-15',
            gender=UserProfile.GENDER_FEMALE,
            education_level=UserProfile.EDUCATION_UNIVERSITY,
            created_by=created_by,
        )
        self.stdout.write(self.style.SUCCESS(f'  Created client: {CLIENT_EMAIL}'))
        return user

    def _create_projects(self, client_user, admin_user):
        if Project.objects.filter(client=client_user).exists():
            self.stdout.write(f'  Projects already exist for {client_user.email}')
            ecommerce_project = Project.objects.filter(client=client_user, name='Plataforma E-commerce').first()
            inventory_project = Project.objects.filter(client=client_user, name='App Móvil Inventarios').first()
            if ecommerce_project:
                self._create_requirements(ecommerce_project)
                self._create_change_requests(ecommerce_project, client_user, admin_user)
                self._create_deliverables(ecommerce_project, admin_user)
                self._create_bug_reports(ecommerce_project, client_user, admin_user)
                self._create_subscription(ecommerce_project)
            self._create_collection_accounts(
                ecommerce_project, inventory_project, client_user, admin_user,
            )
            if ecommerce_project:
                self._create_extended_seed_data(admin_user, client_user, ecommerce_project)
            return

        proposal = self._create_demo_proposal(client_user)

        today = date.today()

        ecommerce_project = Project.objects.create(
            name='Plataforma E-commerce',
            description='Desarrollo de tienda en línea con catálogo de productos, carrito de compras, pasarela de pagos y panel de administración.',
            client=client_user,
            status=Project.STATUS_ACTIVE,
            progress=18,
            start_date=today - timedelta(days=30),
            estimated_end_date=today + timedelta(days=60),
        )

        prop_deliverable = Deliverable.objects.create(
            project=ecommerce_project,
            category=Deliverable.CATEGORY_DOCUMENTS,
            title=(proposal.title or 'Propuesta comercial')[:300],
            description='',
            file=None,
            uploaded_by=admin_user,
        )
        proposal.deliverable = prop_deliverable
        proposal.save(update_fields=['deliverable_id'])

        Project.objects.create(
            name='App Móvil Inventarios',
            description='Aplicación móvil para gestión de inventario en tiempo real con lector de códigos de barras y sincronización con ERP.',
            client=client_user,
            status=Project.STATUS_PAUSED,
            progress=15,
            start_date=today - timedelta(days=10),
            estimated_end_date=today + timedelta(days=120),
        )

        self.stdout.write(self.style.SUCCESS(f'  Created 2 demo projects for {client_user.email}'))

        self._create_requirements(ecommerce_project)
        self._create_change_requests(ecommerce_project, client_user, admin_user)
        self._create_deliverables(ecommerce_project, admin_user)
        self._create_bug_reports(ecommerce_project, client_user, admin_user)
        self._create_subscription(ecommerce_project)

        inventory_project = Project.objects.filter(client=client_user, name='App Móvil Inventarios').first()
        self._create_collection_accounts(
            ecommerce_project, inventory_project, client_user, admin_user,
        )
        self._create_extended_seed_data(admin_user, client_user, ecommerce_project)

    def _create_extended_seed_data(self, admin_user, client_user, ecommerce_project):
        """Extra rows for payments UI, notifications, comments, markdown docs (idempotent)."""
        self._extend_subscription_payments(ecommerce_project)
        self._create_seed_notifications(admin_user, client_user, ecommerce_project)
        self._create_seed_comments(ecommerce_project, admin_user, client_user)
        self._create_seed_markdown_documents(admin_user, client_user, ecommerce_project)

    def _extend_subscription_payments(self, project):
        sub = HostingSubscription.objects.filter(project=project).first()
        if not sub:
            return
        marker = 'seed payment diversity'
        if Payment.objects.filter(subscription=sub, description__icontains=marker).exists():
            return
        today = date.today()
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — next cycle ({marker})',
            billing_period_start=today + timedelta(days=90),
            billing_period_end=today + timedelta(days=179),
            due_date=today + timedelta(days=14),
            status=Payment.STATUS_PENDING,
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — overdue ({marker})',
            billing_period_start=today - timedelta(days=180),
            billing_period_end=today - timedelta(days=91),
            due_date=today - timedelta(days=30),
            status=Payment.STATUS_OVERDUE,
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — failed card ({marker})',
            billing_period_start=today - timedelta(days=270),
            billing_period_end=today - timedelta(days=181),
            due_date=today - timedelta(days=120),
            status=Payment.STATUS_FAILED,
        )
        self.stdout.write(self.style.SUCCESS(f'  Added subscription payment diversity rows ({project.name})'))

    def _create_seed_notifications(self, admin_user, client_user, project):
        if Notification.objects.filter(title__startswith=SEED_PREFIX, user=client_user).exists():
            self.stdout.write('  Seed notifications already present')
            return

        deliverable = Deliverable.objects.filter(project=project).first()
        bug = BugReport.objects.filter(deliverable__project=project).first()
        cr = ChangeRequest.objects.filter(project=project).first()

        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_GENERAL,
            title=f'{SEED_PREFIX} Welcome to the project hub',
            message='Synthetic row: use this inbox to test read/unread and deep links.',
            project=project,
            is_read=True,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_DELIVERABLE_UPLOADED,
            title=f'{SEED_PREFIX} New deliverable available',
            message='Synthetic row for deliverable notification styling.',
            project=project,
            deliverable=deliverable,
            related_object_type='deliverable',
            related_object_id=deliverable.id if deliverable else None,
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_CR_STATUS_CHANGED,
            title=f'{SEED_PREFIX} Change request updated',
            message='Synthetic row tied to a change request.',
            project=project,
            related_object_type='change_request',
            related_object_id=cr.id if cr else None,
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_BUG_STATUS_CHANGED,
            title=f'{SEED_PREFIX} Bug status changed',
            message='Synthetic row tied to a bug report.',
            project=project,
            deliverable=bug.deliverable if bug else None,
            related_object_type='bug_report',
            related_object_id=bug.id if bug else None,
            is_read=False,
        )

        Notification.objects.create(
            user=admin_user,
            type=Notification.TYPE_BUG_REPORTED,
            title=f'{SEED_PREFIX} Client reported a bug (sample)',
            message='Synthetic row for admin notification list.',
            project=project,
            deliverable=bug.deliverable if bug else None,
            related_object_type='bug_report',
            related_object_id=bug.id if bug else None,
            is_read=False,
        )
        Notification.objects.create(
            user=admin_user,
            type=Notification.TYPE_CR_CREATED,
            title=f'{SEED_PREFIX} New change request (sample)',
            message='Synthetic row for triage workflows.',
            project=project,
            related_object_type='change_request',
            related_object_id=cr.id if cr else None,
            is_read=True,
        )
        self.stdout.write(self.style.SUCCESS('  Created seed notifications (admin + client)'))

    def _create_seed_comments(self, project, admin_user, client_user):
        if not RequirementComment.objects.filter(content__startswith=SEED_PREFIX).exists():
            req = Requirement.objects.filter(
                deliverable__project=project, status=Requirement.STATUS_IN_PROGRESS,
            ).first()
            if req:
                RequirementComment.objects.create(
                    requirement=req,
                    user=admin_user,
                    content=f'{SEED_PREFIX} Internal: synced scope with backend; no blockers.',
                    is_internal=True,
                )
                RequirementComment.objects.create(
                    requirement=req,
                    user=client_user,
                    content=f'{SEED_PREFIX} Can we prioritize checkout before recommendations?',
                    is_internal=False,
                )
                self.stdout.write(self.style.SUCCESS('  Created seed requirement comments'))

        first_bug = BugReport.objects.filter(deliverable__project=project).order_by('id').first()
        if first_bug and not BugComment.objects.filter(
            bug_report=first_bug,
            content__startswith=SEED_PREFIX,
        ).exists():
            BugComment.objects.create(
                bug_report=first_bug,
                user=client_user,
                content=f'{SEED_PREFIX} A short screen recording would help us reproduce faster.',
                is_internal=False,
            )
            self.stdout.write(self.style.SUCCESS('  Created seed bug follow-up comment'))

    def _create_seed_markdown_documents(self, admin_user, client_user, project):
        """Panel / PDF markdown documents (not collection_account)."""
        from content.models import Document, DocumentType
        from content.services.document_type_codes import MARKDOWN
        from content.services.markdown_parser import markdown_to_blocks

        dt_md = DocumentType.objects.filter(code=MARKDOWN).first()
        if not dt_md:
            self.stdout.write(self.style.WARNING('  Skipping seed markdown documents: DocumentType markdown missing'))
            return

        def meta_block(title, client_label):
            return {
                'title': title,
                'client_name': client_label,
                'cover_type': 'generic',
                'include_portada': True,
                'include_subportada': True,
                'include_contraportada': True,
            }

        title_en = f'{SEED_PREFIX} Markdown playbook (panel PDF)'
        if not Document.objects.filter(title=title_en).exists():
            body = (
                '# Seed playbook\n\n'
                'This **markdown** document tests the admin panel PDF pipeline.\n\n'
                '## Sections\n\n'
                '- Preview\n'
                '- Export\n'
            )
            Document.objects.create(
                document_type=dt_md,
                title=title_en,
                created_by=admin_user,
                client_name='Internal QA',
                language=Document.Language.EN,
                status=Document.Status.PUBLISHED,
                content_markdown=body,
                content_json={'meta': meta_block(title_en, 'Internal QA'), 'blocks': markdown_to_blocks(body)},
            )
            self.stdout.write(self.style.SUCCESS(f'  Created markdown document: {title_en}'))

        title_es = f'{SEED_PREFIX} Guía rápida (ES)'
        if not Document.objects.filter(title=title_es).exists():
            body_es = '# Guía\n\nContenido de prueba **semilla** enlazado al proyecto demo.\n'
            Document.objects.create(
                document_type=dt_md,
                title=title_es,
                created_by=admin_user,
                client_name='TechStartup Co.',
                language=Document.Language.ES,
                status=Document.Status.DRAFT,
                content_markdown=body_es,
                content_json={'meta': meta_block(title_es, 'TechStartup Co.'), 'blocks': markdown_to_blocks(body_es)},
                client_user=client_user,
                project=project,
            )
            self.stdout.write(self.style.SUCCESS(f'  Created markdown document: {title_es}'))

    def _create_demo_proposal(self, client_user):
        """Create a full demo BusinessProposal (all default sections) for TechStartup e-commerce."""
        from copy import deepcopy
        from decimal import Decimal

        from content.demo_technical_document import DEMO_TECHNICAL_DOCUMENT_JSON
        from content.models import BusinessProposal, ProposalSection
        from content.services.proposal_service import ProposalService

        existing = BusinessProposal.objects.filter(
            client_name='TechStartup Co.', title__icontains='E-commerce',
        ).first()
        if existing:
            self.stdout.write(f'  Demo proposal already exists: {existing.title}')
            return existing

        proposal_title = 'Propuesta Plataforma E-commerce — TechStartup Co.'
        proposal = BusinessProposal.objects.create(
            title=proposal_title,
            client_name='TechStartup Co.',
            client_email=client_user.email,
            client_phone='+57 300 123 4567',
            language='es',
            total_investment=Decimal('11000000'),
            currency='COP',
            hosting_percent=30,
            hosting_discount_semiannual=20,
            hosting_discount_quarterly=10,
            status='accepted',
            project_type='ecommerce',
            market_type='b2c',
        )

        default_sections = ProposalService.get_default_sections(language='es')
        inv_base = deepcopy(
            next(s['content_json'] for s in default_sections if s['section_type'] == 'investment')
        )
        inv_base['introText'] = 'La inversión total para este proyecto es:'
        inv_base['totalInvestment'] = '$11.000.000'
        inv_base['currency'] = 'COP'
        inv_base['paymentOptions'] = [
            {'label': '40% al firmar el contrato \u270d\ufe0f', 'description': '$4.400.000 COP'},
            {'label': '30% al aprobar el diseño final \u2705', 'description': '$3.300.000 COP'},
            {'label': '30% al desplegar el sitio web \U0001f680', 'description': '$3.300.000 COP'},
        ]
        inv_base['hostingPlan'] = {
            'title': 'Hosting Cloud 1',
            'description': 'Infraestructura optimizada para alto rendimiento.',
            'hostingPercent': 30,
            'billingTiers': [
                {
                    'frequency': 'semiannual',
                    'months': 6,
                    'discountPercent': 20,
                    'label': 'Semestral',
                    'badge': 'Mejor precio',
                },
                {
                    'frequency': 'quarterly',
                    'months': 3,
                    'discountPercent': 10,
                    'label': 'Trimestral',
                    'badge': '10% dcto',
                },
                {
                    'frequency': 'monthly',
                    'months': 1,
                    'discountPercent': 0,
                    'label': 'Mensual',
                    'badge': '',
                },
            ],
        }
        inv_base['whatsIncluded'] = [
            {'icon': '\U0001f3a8', 'title': 'Diseño', 'description': 'UX/UI personalizado'},
            {'icon': '\u2699\ufe0f', 'title': 'Desarrollo', 'description': 'Frontend y backend a medida'},
            {'icon': '\U0001f680', 'title': 'Despliegue', 'description': 'Puesta en producción'},
        ]

        demo_tech = deepcopy(DEMO_TECHNICAL_DOCUMENT_JSON)
        for epic in demo_tech.get('epics') or []:
            if epic.get('epicKey') == 'storefront':
                reqs = epic.get('requirements') or []
                if not any(r.get('flowKey') == 'flow-wompi-checkout' for r in reqs if isinstance(r, dict)):
                    reqs.append({
                        'flowKey': 'flow-wompi-checkout',
                        'title': 'Integración Wompi en checkout',
                        'description': 'Cobro con tarjeta y PSE (demo plataforma).',
                        'configuration': 'Sandbox',
                        'usageFlow': 'Usuario completa datos → confirma → redirección Wompi.',
                        'priority': 'critical',
                    })
                    epic['requirements'] = reqs
                break

        for section_cfg in default_sections:
            cfg = deepcopy(section_cfg)
            st = cfg['section_type']
            if st == 'greeting':
                cfg['content_json']['clientName'] = 'TechStartup Co.'
                cfg['content_json']['proposalTitle'] = proposal_title
            elif st == 'investment':
                cfg['content_json'] = inv_base
            elif st == 'technical_document':
                cfg['content_json'] = demo_tech
            ProposalSection.objects.create(proposal=proposal, **cfg)

        self.stdout.write(self.style.SUCCESS(f'  Created demo proposal: {proposal.title}'))
        return proposal

    def _create_requirements(self, project):
        if Requirement.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        default_deliverable = (
            Deliverable.objects.filter(project=project)
            .filter(business_proposal__isnull=False)
            .order_by('id')
            .first()
        )
        if not default_deliverable:
            default_deliverable = Deliverable.objects.filter(project=project).order_by('id').first()
        if not default_deliverable:
            default_deliverable = Deliverable.objects.create(
                project=project,
                category=Deliverable.CATEGORY_OTHER,
                title='Alcance inicial',
                description='',
                file=None,
                uploaded_by=project.client,
            )

        reqs = [
            {'title': 'Diseño de la página principal', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 0, 'estimated_hours': 16},
            {'title': 'Catálogo de productos con filtros', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 1, 'estimated_hours': 24},
            {'title': 'Carrito de compras', 'status': 'in_review', 'priority': 'critical', 'module': 'Frontend', 'order': 0, 'estimated_hours': 20},
            {'title': 'Integración pasarela de pagos (Wompi)', 'status': 'in_progress', 'priority': 'critical', 'module': 'Backend', 'order': 0, 'estimated_hours': 32},
            {'title': 'Sistema de autenticación de usuarios', 'status': 'in_progress', 'priority': 'high', 'module': 'Backend', 'order': 1, 'estimated_hours': 12},
            {'title': 'Panel de administración de productos', 'status': 'in_review', 'priority': 'medium', 'module': 'Admin', 'order': 1, 'estimated_hours': 18},
            {'title': 'Notificaciones por email de pedidos', 'status': 'todo', 'priority': 'medium', 'module': 'Backend', 'order': 0, 'estimated_hours': 8},
            {'title': 'Sistema de cupones y descuentos', 'status': 'todo', 'priority': 'low', 'module': 'Backend', 'order': 1, 'estimated_hours': 14},
            {'title': 'Gestión de inventario', 'status': 'todo', 'priority': 'medium', 'module': 'Admin', 'order': 2, 'estimated_hours': 20},
            {'title': 'Reportes de ventas', 'status': 'todo', 'priority': 'low', 'module': 'Admin', 'order': 3, 'estimated_hours': 16},
            {'title': 'Optimización SEO del catálogo', 'status': 'todo', 'priority': 'low', 'module': 'Frontend', 'order': 4, 'estimated_hours': 10},
        ]

        for r in reqs:
            mod = r.get('module', '')
            hours = r.get('estimated_hours')
            meta_parts = []
            if mod:
                meta_parts.append(f'Módulo: {mod}')
            if hours is not None:
                meta_parts.append(f'~{hours} h estimadas')
            description = ' · '.join(meta_parts) if meta_parts else ''
            Requirement.objects.create(
                deliverable=default_deliverable,
                title=r['title'],
                description=description,
                status=r['status'],
                priority=r['priority'],
                order=r.get('order', 0),
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(reqs)} requirements for {project.name}'))

    def _create_change_requests(self, project, client_user, admin_user):
        if ChangeRequest.objects.filter(project=project).exists():
            self.stdout.write(f'  Change requests already exist for {project.name}')
            return

        crs = [
            {
                'title': 'Agregar filtro de rango de precio en catálogo',
                'description': 'Los usuarios necesitan poder filtrar productos por un rango de precio mínimo y máximo, similar a lo que hace MercadoLibre.',
                'module_or_screen': 'Catálogo / Filtros',
                'suggested_priority': 'high',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_APPROVED,
                'admin_response': 'Buen punto, lo incluiremos en el sprint actual. Estimamos 2 días de trabajo.',
                'estimated_cost': 0,
                'estimated_time': '2 días',
            },
            {
                'title': 'Cambiar color del botón de compra a verde',
                'description': 'El botón "Agregar al carrito" actualmente es azul, pero creemos que verde genera más confianza para la acción de compra.',
                'module_or_screen': 'Producto detalle',
                'suggested_priority': 'low',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_EVALUATING,
                'admin_response': '',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Integrar login con Google',
                'description': 'Queremos que los clientes puedan iniciar sesión con su cuenta de Google además del email/password.',
                'module_or_screen': 'Autenticación',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_PENDING,
                'admin_response': '',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Agregar sección de productos recomendados',
                'description': 'En la página de detalle de producto, mostrar una sección "También te puede interesar" con productos relacionados.',
                'module_or_screen': 'Producto detalle',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_REJECTED,
                'admin_response': 'Este cambio requiere un motor de recomendaciones que está fuera del alcance actual. Lo evaluaremos para la fase 2.',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Notificación WhatsApp cuando hay pedido nuevo',
                'description': 'Además del email, necesitamos una notificación por WhatsApp cuando un cliente realiza un pedido.',
                'module_or_screen': 'Notificaciones',
                'suggested_priority': 'high',
                'is_urgent': True,
                'status': ChangeRequest.STATUS_NEEDS_CLARIFICATION,
                'admin_response': '¿Quieres recibir la notificación solo tú o también el equipo de bodega?',
                'estimated_cost': None,
                'estimated_time': '',
            },
        ]

        for cr_data in crs:
            cr = ChangeRequest.objects.create(
                project=project,
                created_by=client_user,
                title=cr_data['title'],
                description=cr_data['description'],
                module_or_screen=cr_data.get('module_or_screen', ''),
                suggested_priority=cr_data['suggested_priority'],
                is_urgent=cr_data.get('is_urgent', False),
                status=cr_data['status'],
                admin_response=cr_data.get('admin_response', ''),
                estimated_cost=cr_data.get('estimated_cost'),
                estimated_time=cr_data.get('estimated_time', ''),
            )

            if cr_data['admin_response']:
                ChangeRequestComment.objects.create(
                    change_request=cr,
                    user=admin_user,
                    content=cr_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(crs)} change requests for {project.name}'))

    def _create_bug_reports(self, project, client_user, admin_user):
        if BugReport.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Bug reports already exist for {project.name}')
            return

        deliverable_list = list(
            Deliverable.objects.filter(project=project).order_by('id'),
        )
        if not deliverable_list:
            self.stdout.write(self.style.WARNING(f'  Skipping bug reports — no deliverables for {project.name}'))
            return

        bugs = [
            {
                'title': 'Botón "Agregar al carrito" no responde en móvil',
                'description': 'En dispositivos móviles (iPhone 14, Safari), al tocar el botón de agregar al carrito no pasa nada.',
                'severity': BugReport.SEVERITY_CRITICAL,
                'steps_to_reproduce': [
                    'Abrir la tienda desde un iPhone',
                    'Navegar a cualquier producto',
                    'Tocar el botón "Agregar al carrito"',
                    'No sucede nada, el carrito sigue vacío',
                ],
                'expected_behavior': 'El producto debería agregarse al carrito y mostrar confirmación.',
                'actual_behavior': 'El botón no responde al touch en Safari iOS.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'iPhone 14 / Safari 17',
                'is_recurring': True,
                'status': BugReport.STATUS_CONFIRMED,
                'admin_response': 'Confirmado. Parece un problema con el event handler en Safari. Lo priorizamos.',
            },
            {
                'title': 'Imágenes del catálogo cargan muy lento',
                'description': 'Las imágenes de productos tardan más de 5 segundos en cargar, especialmente en conexiones 4G.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Abrir el catálogo de productos',
                    'Hacer scroll por la lista',
                    'Las imágenes aparecen como placeholder gris por varios segundos',
                ],
                'expected_behavior': 'Las imágenes deberían cargar en menos de 2 segundos.',
                'actual_behavior': 'Tardan 5-8 segundos. No hay lazy loading.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome 120 / Windows',
                'is_recurring': True,
                'status': BugReport.STATUS_FIXING,
                'admin_response': 'Vamos a implementar lazy loading y optimización de imágenes.',
            },
            {
                'title': 'Error 500 al buscar con caracteres especiales',
                'description': 'Si se busca un producto usando comillas o el símbolo & en el buscador, da error de servidor.',
                'severity': BugReport.SEVERITY_MEDIUM,
                'steps_to_reproduce': [
                    'Ir al buscador de productos',
                    'Escribir: camiseta "roja"',
                    'Presionar Enter',
                    'Aparece página de error 500',
                ],
                'expected_behavior': 'Debería mostrar resultados o un mensaje de "sin resultados".',
                'actual_behavior': 'Error 500 Internal Server Error.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome / macOS',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
            {
                'title': 'Precio muestra $0 en algunos productos',
                'description': 'Algunos productos muestran $0 como precio aunque en el admin tienen precio configurado.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Navegar al catálogo',
                    'Filtrar por categoría "Electrónicos"',
                    'Ver que 2 productos muestran $0',
                ],
                'expected_behavior': 'Todos los productos deberían mostrar su precio real.',
                'actual_behavior': 'Algunos muestran $0.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Cualquier navegador',
                'is_recurring': False,
                'status': BugReport.STATUS_RESOLVED,
                'admin_response': 'Era un problema de caché. Ya se limpió y se agregó invalidación automática.',
            },
            {
                'title': 'Formulario de contacto no envía en Firefox',
                'description': 'El formulario de contacto del footer no envía en Firefox. El botón se queda en estado "Enviando..." indefinidamente.',
                'severity': BugReport.SEVERITY_LOW,
                'steps_to_reproduce': [
                    'Abrir la tienda en Firefox',
                    'Ir al footer y llenar el formulario de contacto',
                    'Hacer clic en Enviar',
                    'El botón cambia a "Enviando..." y nunca termina',
                ],
                'expected_behavior': 'El formulario debería enviarse y mostrar mensaje de confirmación.',
                'actual_behavior': 'Se queda cargando indefinidamente.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Firefox 121 / Windows',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
        ]

        for i, bug_data in enumerate(bugs):
            dlv = deliverable_list[i % len(deliverable_list)]
            bug = BugReport.objects.create(
                deliverable=dlv,
                reported_by=client_user,
                title=bug_data['title'],
                description=bug_data['description'],
                severity=bug_data['severity'],
                steps_to_reproduce=bug_data['steps_to_reproduce'],
                expected_behavior=bug_data['expected_behavior'],
                actual_behavior=bug_data['actual_behavior'],
                environment=bug_data['environment'],
                device_browser=bug_data.get('device_browser', ''),
                is_recurring=bug_data.get('is_recurring', False),
                status=bug_data['status'],
                admin_response=bug_data.get('admin_response', ''),
            )

            if bug_data['admin_response']:
                BugComment.objects.create(
                    bug_report=bug,
                    user=admin_user,
                    content=bug_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(bugs)} bug reports for {project.name}'))

    def _create_deliverables(self, project, admin_user):
        marker_title = 'Wireframes página principal'
        if Deliverable.objects.filter(project=project, title=marker_title).exists():
            self.stdout.write(f'  File deliverables already seeded for {project.name}')
            return

        from django.core.files.base import ContentFile

        deliverables = [
            {
                'title': 'Wireframes página principal',
                'description': 'Wireframes de baja fidelidad para la estructura de la home page.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'wireframes-home-v1.pdf',
            },
            {
                'title': 'Guía de estilos UI',
                'description': 'Colores, tipografías, espaciados y componentes del sistema de diseño.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'style-guide-v1.pdf',
            },
            {
                'title': 'Credenciales Wompi Sandbox',
                'description': 'Llaves de API para pruebas en sandbox de la pasarela de pagos.',
                'category': Deliverable.CATEGORY_CREDENTIALS,
                'filename': 'wompi-sandbox-keys.txt',
            },
            {
                'title': 'Manual de usuario',
                'description': 'Documentación de uso del panel de administración de productos.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'manual-admin-v1.pdf',
            },
            {
                'title': 'APK Android beta',
                'description': 'Build de prueba para Android. Requiere permisos de instalación de fuentes desconocidas.',
                'category': Deliverable.CATEGORY_APKS,
                'filename': 'ecommerce-beta-v0.1.apk',
            },
        ]

        from accounts.models import DeliverableVersion

        for d_data in deliverables:
            placeholder = ContentFile(b'placeholder content', name=d_data['filename'])

            d = Deliverable.objects.create(
                project=project,
                uploaded_by=admin_user,
                title=d_data['title'],
                description=d_data['description'],
                category=d_data['category'],
                file=placeholder,
                current_version=1,
            )

            DeliverableVersion.objects.create(
                deliverable=d,
                file=placeholder,
                version_number=1,
                uploaded_by=admin_user,
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(deliverables)} deliverables for {project.name}'))

    def _create_subscription(self, project):
        if HostingSubscription.objects.filter(project=project).exists():
            self.stdout.write(f'  Subscription already exists for {project.name}')
            return

        from decimal import Decimal

        today = date.today()

        sub = HostingSubscription.objects.create(
            project=project,
            plan=HostingSubscription.PLAN_QUARTERLY,
            base_monthly_amount=Decimal('330000'),
            discount_percent=10,
            effective_monthly_amount=Decimal('297000'),
            billing_amount=Decimal('891000'),
            status=HostingSubscription.STATUS_ACTIVE,
            start_date=today - timedelta(days=90),
            next_billing_date=today + timedelta(days=90),
        )

        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today - timedelta(days=90),
            billing_period_end=today - timedelta(days=1),
            due_date=today - timedelta(days=90),
            status=Payment.STATUS_PAID,
            paid_at=timezone.now() - timedelta(days=88),
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today,
            billing_period_end=today + timedelta(days=89),
            due_date=today,
            status=Payment.STATUS_PAID,
            paid_at=timezone.now() - timedelta(hours=2),
        )

        self.stdout.write(self.style.SUCCESS(f'  Created subscription + 2 payments for {project.name}'))

    def _create_collection_accounts(self, ecommerce_project, inventory_project, client_user, admin_user):
        """
        Seed collection_account documents for platform QA: draft, issued, paid, cancelled, overdue.
        Titles are prefixed with [Demo] for easy identification.
        """
        from decimal import Decimal

        from content.models import (
            Document,
            DocumentCollectionAccount,
            DocumentItem,
            DocumentPaymentMethod,
            IssuerProfile,
        )
        from content.services.collection_account_service import (
            issue_collection_account,
            mark_collection_account_cancelled,
            mark_collection_account_paid,
            recalculate_document_totals,
        )
        from content.services.document_type_utils import get_collection_account_document_type

        if not ecommerce_project:
            self.stdout.write(self.style.WARNING('  Skipping collection accounts: no e-commerce project'))
            return

        if Document.objects.filter(
            project=ecommerce_project,
            document_type__code='collection_account',
        ).exists():
            self.stdout.write('  Collection accounts already seeded for demo project')
            return

        issuer = IssuerProfile.objects.order_by('pk').first()
        if not issuer:
            self.stdout.write(
                self.style.WARNING(
                    '  Skipping collection accounts: run migrations (IssuerProfile / DocumentType)',
                ),
            )
            return

        try:
            doc_type = get_collection_account_document_type()
        except Exception:
            self.stdout.write(
                self.style.WARNING('  Skipping collection accounts: collection_account DocumentType missing'),
            )
            return

        today = date.today()

        def new_draft(title, project, *, billing_concept, payment_term_days=30, support_ref=''):
            doc = Document.objects.create(
                title=title,
                document_type=doc_type,
                commercial_status=Document.CommercialStatus.DRAFT,
                project=project,
                client_user=client_user,
                currency='COP',
                city='Bogotá',
                notes='Demo seed data for platform tests.',
                created_by=admin_user,
                updated_by=admin_user,
            )
            DocumentCollectionAccount.objects.create(
                document=doc,
                billing_concept=billing_concept,
                payment_term_type=DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE,
                payment_term_days=payment_term_days,
                support_reference=support_ref or f'DEMO-PROJ-{project.id}',
            )
            return doc

        def add_items(doc, rows):
            for idx, row in enumerate(rows):
                qty = Decimal(str(row['quantity']))
                up = Decimal(str(row['unit_price']))
                da = Decimal(str(row.get('discount_amount', '0')))
                ta = Decimal(str(row.get('tax_amount', '0')))
                lt = row.get('line_total')
                if lt is None:
                    lt = qty * up - da + ta
                else:
                    lt = Decimal(str(lt))
                DocumentItem.objects.create(
                    document=doc,
                    position=row.get('position', idx),
                    item_type=row.get('item_type', DocumentItem.ItemType.SERVICE),
                    description=row['description'],
                    quantity=qty,
                    unit_price=up,
                    discount_amount=da,
                    tax_amount=ta,
                    line_total=lt,
                )
            recalculate_document_totals(doc)
            doc.save()

        def add_bank_transfer(doc):
            DocumentPaymentMethod.objects.create(
                document=doc,
                payment_method_type=DocumentPaymentMethod.MethodType.BANK_TRANSFER,
                bank_name='Bancolombia',
                account_type='checking',
                account_number='1234567890',
                account_holder_name='ProjectApp SAS',
                account_holder_identification='900123456',
                payment_instructions='Reference: invoice number. Email receipt to finance@projectapp.co',
                is_primary=True,
            )

        # 1) Draft only (admin sees it; client list hides drafts)
        d1 = new_draft(
            '[Demo] Draft collection account',
            ecommerce_project,
            billing_concept='E-commerce milestone 1 — pending approval',
        )
        add_items(
            d1,
            [
                {
                    'description': 'UX/UI design sprint (40h)',
                    'quantity': '1',
                    'unit_price': '4400000',
                    'discount_amount': '0',
                    'tax_amount': '0',
                },
            ],
        )

        # 2) Issued + payment method (client visible, PDF-ready)
        d2 = new_draft(
            '[Demo] Issued collection account',
            ecommerce_project,
            billing_concept='Development installment — design sign-off',
            payment_term_days=15,
        )
        add_items(
            d2,
            [
                {
                    'description': 'Payment milestone: 30% after design approval',
                    'quantity': '1',
                    'unit_price': '3300000',
                    'item_type': DocumentItem.ItemType.ADVANCE,
                },
                {
                    'description': 'Hosting setup (quarterly)',
                    'quantity': '1',
                    'unit_price': '891000',
                    'item_type': DocumentItem.ItemType.HOSTING,
                },
            ],
        )
        add_bank_transfer(d2)
        d2 = Document.objects.get(pk=d2.pk)
        issue_collection_account(d2, issuer=issuer, acting_user=admin_user)

        # 3) Paid (terminal state)
        d3 = new_draft(
            '[Demo] Paid collection account',
            ecommerce_project,
            billing_concept='Initial deposit — contract signature',
            payment_term_days=7,
        )
        add_items(
            d3,
            [
                {
                    'description': '40% at contract signature',
                    'quantity': '1',
                    'unit_price': '4400000',
                },
            ],
        )
        add_bank_transfer(d3)
        d3 = Document.objects.get(pk=d3.pk)
        issue_collection_account(d3, issuer=issuer, acting_user=admin_user)
        mark_collection_account_paid(d3, acting_user=admin_user)

        # 4) Cancelled from draft
        d4 = new_draft(
            '[Demo] Cancelled from draft',
            ecommerce_project,
            billing_concept='Superseded by revised quote',
        )
        add_items(
            d4,
            [{'description': 'Placeholder line', 'quantity': '1', 'unit_price': '100'}],
        )
        d4 = Document.objects.get(pk=d4.pk)
        mark_collection_account_cancelled(d4, acting_user=admin_user)

        # 5) Issued + overdue (due date in the past)
        d5 = new_draft(
            '[Demo] Overdue collection account',
            ecommerce_project,
            billing_concept='Balance due — integration phase',
            payment_term_days=14,
        )
        add_items(
            d5,
            [
                {
                    'description': 'Wompi integration + testing',
                    'quantity': '1',
                    'unit_price': '2500000',
                },
            ],
        )
        add_bank_transfer(d5)
        d5 = Document.objects.get(pk=d5.pk)
        issue_collection_account(d5, issuer=issuer, acting_user=admin_user)
        Document.objects.filter(pk=d5.pk).update(due_date=today - timedelta(days=20))

        # 6) Issued then cancelled (voided after issue)
        d6 = new_draft(
            '[Demo] Cancelled after issue',
            ecommerce_project,
            billing_concept='Invoice void — duplicate entry',
            payment_term_days=10,
        )
        add_items(
            d6,
            [{'description': 'Duplicate billing correction', 'quantity': '1', 'unit_price': '500000'}],
        )
        d6 = Document.objects.get(pk=d6.pk)
        issue_collection_account(d6, issuer=issuer, acting_user=admin_user)
        d6 = Document.objects.get(pk=d6.pk)
        mark_collection_account_cancelled(d6, acting_user=admin_user)

        # 7) Second project — small issued document
        if inventory_project:
            d7 = new_draft(
                '[Demo] Inventory app — discovery invoice',
                inventory_project,
                billing_concept='Discovery workshop (2 days)',
                payment_term_days=20,
            )
            add_items(
                d7,
                [{'description': 'Workshop + backlog', 'quantity': '2', 'unit_price': '800000'}],
            )
            d7 = Document.objects.get(pk=d7.pk)
            issue_collection_account(d7, issuer=issuer, acting_user=admin_user)

        self.stdout.write(
            self.style.SUCCESS(
                '  Created demo collection accounts (draft, issued, paid, cancelled, overdue, multi-project)',
            ),
        )

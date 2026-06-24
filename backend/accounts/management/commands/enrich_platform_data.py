"""Management command — enrich the platform graph with sub-models that the base
``seed_platform_data`` does not (or only sparsely) create.

Additive and idempotent: safe to run after ``seed_platform_data``. It tops up:

* ``PaymentHistory`` transition logs for every ``Payment`` lacking them,
* ``ProjectDataModelEntity`` rows per project (real data-model state),
* ``DeliverableClientFolder`` / ``DeliverableClientUpload`` / ``DeliverableFile``
  for a sample of deliverables,
* extra ``Notification`` rows up to a target volume,

and ensures admin-settings singletons exist (``CompanySettings``,
``EmailTemplateConfig``, default configs, a few ``SavedFilterTab``).
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import (
    Deliverable,
    DeliverableClientFolder,
    DeliverableClientUpload,
    DeliverableFile,
    Notification,
    Payment,
    PaymentHistory,
    Project,
    ProjectDataModelEntity,
    SavedFilterTab,
    UserProfile,
)

User = get_user_model()

# Coherent status paths per current Payment status (keys are status string values).
HISTORY_PATHS = {
    Payment.STATUS_PAID: [('pending', 'processing', 'system'), ('processing', 'paid', 'webhook')],
    Payment.STATUS_PROCESSING: [('pending', 'processing', 'wompi_link')],
    Payment.STATUS_FAILED: [('pending', 'processing', 'wompi_link'), ('processing', 'failed', 'webhook')],
    Payment.STATUS_OVERDUE: [('pending', 'overdue', 'system')],
    Payment.STATUS_PENDING: [('pending', 'pending', 'system')],
}

NOTIFICATION_SPECS = [
    (Notification.TYPE_DELIVERABLE_UPLOADED, 'Nuevo entregable disponible',
     'Se subió un nuevo entregable a tu proyecto.'),
    (Notification.TYPE_BUG_STATUS_CHANGED, 'Estado de reporte actualizado',
     'Tu reporte de error cambió de estado.'),
    (Notification.TYPE_CR_STATUS_CHANGED, 'Solicitud de cambio actualizada',
     'Tu solicitud de cambio fue evaluada por el equipo.'),
    (Notification.TYPE_REQUIREMENT_APPROVED, 'Requerimiento aprobado',
     'Un requerimiento fue aprobado y pasa a desarrollo.'),
    (Notification.TYPE_COMMENT_ADDED, 'Nuevo comentario',
     'Hay un nuevo comentario en tu proyecto.'),
    (Notification.TYPE_GENERAL, 'Bienvenido a la plataforma',
     'Gracias por confiar en nosotros. Aquí verás el avance de tu proyecto.'),
]

ENTITY_SPECS = [
    ('Usuario', 'Cuenta de acceso a la plataforma.', 'email, nombre, rol, fecha_registro', 'Tiene muchos Pedidos'),
    ('Producto', 'Ítem del catálogo.', 'nombre, precio, stock, categoria', 'Pertenece a una Categoría'),
    ('Pedido', 'Orden de compra del cliente.', 'numero, total, estado, fecha', 'Pertenece a un Usuario'),
    ('Pago', 'Transacción asociada a un pedido.', 'monto, metodo, estado, referencia_wompi', 'Pertenece a un Pedido'),
    ('Categoría', 'Agrupación de productos.', 'nombre, slug, orden', 'Tiene muchos Productos'),
]


class Command(BaseCommand):
    help = 'Enrich the platform graph with payment history, data-model entities, ' \
           'deliverable uploads, notifications and admin-settings singletons.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--notifications', type=int, default=40,
            help='Target total number of notifications (default: 40).',
        )

    def handle(self, *args, **options):
        rng = random.Random(23)
        admin = User.objects.filter(is_staff=True).first()

        self._payment_history(rng)
        self._data_model_entities(admin)
        self._deliverable_uploads(rng, admin)
        self._notifications(rng, options['notifications'])
        self._admin_settings(admin)

        self.stdout.write(self.style.SUCCESS('Platform graph enriched.'))

    def _payment_history(self, rng):
        with_history = set(PaymentHistory.objects.values_list('payment_id', flat=True))
        rows = []
        for payment in Payment.objects.exclude(id__in=with_history):
            path = HISTORY_PATHS.get(payment.status, HISTORY_PATHS[Payment.STATUS_PENDING])
            rows += [
                PaymentHistory(
                    payment=payment, from_status=from_s, to_status=to_s,
                    source=source, metadata={'seed': True},
                )
                for from_s, to_s, source in path
            ]
        PaymentHistory.objects.bulk_create(rows)
        self.stdout.write(self.style.SUCCESS(f'  PaymentHistory rows created: {len(rows)}'))

    def _data_model_entities(self, admin):
        seeded = set(ProjectDataModelEntity.objects.values_list('project_id', flat=True))
        rows = []
        for project in Project.objects.exclude(id__in=seeded):
            rows += [
                ProjectDataModelEntity(
                    project=project, name=name, description=desc,
                    key_fields=key_fields, relationship=relationship,
                )
                for name, desc, key_fields, relationship in ENTITY_SPECS
            ]
        ProjectDataModelEntity.objects.bulk_create(rows)
        self.stdout.write(self.style.SUCCESS(f'  ProjectDataModelEntity rows created: {len(rows)}'))

    def _deliverable_uploads(self, rng, admin):
        folders = uploads = files = 0
        deliverables = list(Deliverable.objects.select_related('project').all())
        for deliverable in deliverables:
            client = deliverable.project.client if deliverable.project_id else None
            # Attachment files (admin-provided) for ~half of deliverables.
            if rng.random() < 0.5 and not deliverable.attachment_files.exists():
                DeliverableFile.objects.create(
                    deliverable=deliverable,
                    file=f'deliverables/files/{deliverable.pk}/anexo.pdf',
                    title='Anexo de referencia',
                    category=deliverable.category,
                    uploaded_by=admin,
                )
                files += 1
            # Client upload folder + PDFs for ~40% of deliverables.
            if client and rng.random() < 0.4 and not deliverable.client_folders.exists():
                folder = DeliverableClientFolder.objects.create(
                    deliverable=deliverable,
                    name='Documentos del cliente',
                    created_by=client,
                    order=0,
                )
                folders += 1
                for k in range(rng.randint(1, 2)):
                    DeliverableClientUpload.objects.create(
                        deliverable=deliverable,
                        folder=folder,
                        file=f'deliverables/client/{deliverable.pk}/comprobante-{k + 1}.pdf',
                        title=f'Comprobante {k + 1}',
                        uploaded_by=client,
                    )
                    uploads += 1
        self.stdout.write(self.style.SUCCESS(
            f'  Deliverable client folders={folders} uploads={uploads} attachment files={files}'))

    def _notifications(self, rng, target):
        existing = Notification.objects.count()
        if existing >= target:
            self.stdout.write(self.style.SUCCESS(
                f'  Notifications already at {existing} (>= {target}) — skipped'))
            return
        projects = list(Project.objects.select_related('client').all())
        client_users = [p.client for p in projects if p.client_id]
        if not client_users:
            client_users = [
                p.user for p in UserProfile.objects.filter(
                    role=UserProfile.ROLE_CLIENT).select_related('user')
            ]
        if not client_users:
            self.stdout.write(self.style.WARNING('  No client users — notifications skipped'))
            return

        rows = []
        for i in range(target - existing):
            ntype, title, message = NOTIFICATION_SPECS[i % len(NOTIFICATION_SPECS)]
            user = rng.choice(client_users)
            project = rng.choice(projects) if projects else None
            rows.append(Notification(
                user=user,
                type=ntype,
                title=title,
                message=message,
                project=project if (project and project.client_id == user.id) else None,
                is_read=rng.random() < 0.4,
            ))
        Notification.objects.bulk_create(rows)
        self.stdout.write(self.style.SUCCESS(f'  Notifications created: {len(rows)}'))

    def _admin_settings(self, admin):
        from content.models import (
            CompanySettings,
            DiagnosticDefaultConfig,
            EmailTemplateConfig,
            ProposalDefaultConfig,
        )

        CompanySettings.objects.get_or_create(
            pk=1,
            defaults={
                'contractor_full_name': 'ProjectApp S.A.S.',
                'contractor_nit': '901.234.567-8',
                'contractor_email': 'contratos@projectapp.dev',
                'bank_name': 'Bancolombia',
                'bank_account_type': 'Ahorros',
                'bank_account_number': '123-456789-00',
                'contract_city': 'Bogotá',
            },
        )
        for key in ('proposal_sent', 'proposal_reminder'):
            EmailTemplateConfig.objects.get_or_create(
                template_key=key, defaults={'content_overrides': {}, 'is_active': True})

        # Default configs are usually created by data migrations; ensure-exist defensively.
        for lang in ('es', 'en'):
            ProposalDefaultConfig.objects.get_or_create(language=lang)
            DiagnosticDefaultConfig.objects.get_or_create(language=lang)

        if admin:
            SavedFilterTab.objects.get_or_create(
                user=admin, view='proposal', name='Aceptadas',
                defaults={'filters': {'status': ['accepted']}, 'order': 0},
            )
            SavedFilterTab.objects.get_or_create(
                user=admin, view='client', name='Onboarding pendiente',
                defaults={'filters': {'is_onboarded': False}, 'order': 0},
            )
        self.stdout.write(self.style.SUCCESS('  Admin settings ensured.'))

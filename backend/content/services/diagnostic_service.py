"""Service layer for the WebAppDiagnostic feature.

Diagnostics are modeled as a sequence of JSON-driven ``DiagnosticSection``
rows (one per section_type). A seed from ``content.seeds.diagnostic_template``
populates a new diagnostic with the default narrative; from there the admin
edits each section through the section editor.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from accounts.services.proposal_client_service import build_client_display_name
from content.models import (
    DiagnosticChangeLog,
    DiagnosticSection,
    WebAppDiagnostic,
)
from content.seeds.diagnostic_template import default_sections
from content.utils import format_cop_email


def _classify_size(value: int, thresholds: tuple[int, int]) -> str:
    low, high = thresholds
    if value <= 0:
        return ''
    if value < low:
        return 'Pequeña'
    if value <= high:
        return 'Mediana'
    return 'Grande'


def build_render_context(diagnostic: WebAppDiagnostic) -> dict:
    """Build the variable map used by section components to hydrate headings.

    Kept for backward compatibility with email templates and for the
    radiography section renderer which shows pricing/metrics pulled from
    ``diagnostic.radiography`` + pricing fields.
    """
    radiography = diagnostic.radiography or {}
    payment = diagnostic.payment_terms or {}
    stack = radiography.get('stack', {}) or {}
    backend_stack = stack.get('backend', {}) or {}
    frontend_stack = stack.get('frontend', {}) or {}
    modules = radiography.get('modules') or []

    if isinstance(modules, list) and modules:
        modules_list = '\n'.join(
            f'{i}. {m}' for i, m in enumerate(modules, start=1)
        )
        modules_count = len(modules)
    else:
        modules_list = ''
        modules_count = radiography.get('modules_count', 0) or 0

    entities = radiography.get('entities_count', 0) or 0
    routes = radiography.get('routes_total', 0) or 0
    fe_routes = radiography.get('frontend_routes_count', 0) or 0
    components = radiography.get('components_count', 0) or 0
    integrations = radiography.get('external_integrations', 0) or 0

    size_label = ''
    if diagnostic.size_category:
        size_label = WebAppDiagnostic.SizeCategory(diagnostic.size_category).label

    return {
        'client_name': build_client_display_name(diagnostic.client),
        'investment_amount': format_cop_email(diagnostic.investment_amount),
        'currency': diagnostic.currency or '',
        'payment_initial_pct': payment.get('initial_pct', ''),
        'payment_final_pct': payment.get('final_pct', ''),
        'duration_label': diagnostic.duration_label or '',
        'size_category_label': size_label,

        'stack_backend_name': backend_stack.get('name', ''),
        'stack_backend_version': backend_stack.get('version', ''),
        'stack_frontend_name': frontend_stack.get('name', ''),
        'stack_frontend_version': frontend_stack.get('version', ''),

        'migrations_count': radiography.get('migrations_count', ''),
        'entities_count': entities,
        'routes_total': routes,
        'routes_public': radiography.get('routes_public', ''),
        'routes_protected': radiography.get('routes_protected', ''),
        'controllers_count': radiography.get('controllers_count', ''),
        'controllers_disconnected': radiography.get('controllers_disconnected', ''),
        'frontend_routes_count': fe_routes,
        'components_count': components,
        'external_integrations': integrations,
        'modules_count': modules_count,
        'modules_list': modules_list,
        'test_files_count': radiography.get('test_files_count', ''),
        'test_coverage_label': radiography.get('test_coverage_label', ''),
        'ci_files_count': radiography.get('ci_files_count', ''),
        'docker_files_count': radiography.get('docker_files_count', ''),

        'entities_size': _classify_size(int(entities or 0), (15, 50)),
        'routes_size': _classify_size(int(routes or 0), (30, 100)),
        'frontend_routes_size': _classify_size(int(fe_routes or 0), (15, 50)),
        'components_size': _classify_size(int(components or 0), (20, 80)),
        'integrations_size': _classify_size(int(integrations or 0), (3, 7)),
        'modules_size': _classify_size(int(modules_count or 0), (4, 8)),
    }


def seed_sections(diagnostic: WebAppDiagnostic) -> list[DiagnosticSection]:
    """Create the default 8 sections for a diagnostic from the JSON seed."""
    return DiagnosticSection.objects.bulk_create([
        DiagnosticSection(
            diagnostic=diagnostic,
            section_type=spec['section_type'],
            title=spec['title'],
            order=spec['order'],
            is_enabled=spec['is_enabled'],
            visibility=spec['visibility'],
            content_json=spec['content_json'],
        )
        for spec in default_sections()
    ])


def reset_section(section: DiagnosticSection) -> DiagnosticSection:
    """Restore a single section's ``content_json`` from the JSON seed."""
    for spec in default_sections():
        if spec['section_type'] == section.section_type:
            section.content_json = spec['content_json']
            section.title = spec['title']
            section.visibility = spec['visibility']
            section.is_enabled = spec['is_enabled']
            section.save(update_fields=[
                'content_json', 'title', 'visibility', 'is_enabled',
            ])
            return section
    return section


@transaction.atomic
def create_diagnostic(
    *,
    client,
    language: str = 'es',
    title: str = '',
    created_by=None,
) -> WebAppDiagnostic:
    """Create a diagnostic and seed its 8 JSON sections."""
    if not title:
        title = f'Diagnóstico — {build_client_display_name(client)}'

    diagnostic = WebAppDiagnostic.objects.create(
        client=client,
        language=language,
        title=title,
        created_by=created_by,
    )
    seed_sections(diagnostic)
    log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.CREATED,
        description='Diagnóstico creado desde plantilla.',
        actor_type=DiagnosticChangeLog.ActorType.SELLER,
    )
    return diagnostic


def transition_status(
    diagnostic: WebAppDiagnostic,
    new_status: str,
    *,
    actor_type: str = '',
) -> WebAppDiagnostic:
    """Validate transition + stamp the matching timestamp."""
    if not diagnostic.can_transition_to(new_status):
        raise ValueError(
            f'invalid_transition: {diagnostic.status} → {new_status}'
        )

    update_fields = ['status', 'updated_at']
    old_status = diagnostic.status
    diagnostic.status = new_status
    now = timezone.now()

    if new_status == WebAppDiagnostic.Status.SENT:
        if diagnostic.initial_sent_at is None:
            diagnostic.initial_sent_at = now
            update_fields.append('initial_sent_at')
        else:
            diagnostic.final_sent_at = now
            update_fields.append('final_sent_at')
    elif new_status in (
        WebAppDiagnostic.Status.ACCEPTED,
        WebAppDiagnostic.Status.REJECTED,
    ):
        diagnostic.responded_at = now
        update_fields.append('responded_at')

    diagnostic.save(update_fields=update_fields)

    log_change(
        diagnostic,
        change_type=DiagnosticChangeLog.ChangeType.STATUS_CHANGE,
        field_name='status',
        old_value=old_status,
        new_value=new_status,
        description=f'Estado: {old_status} → {new_status}',
        actor_type=actor_type or DiagnosticChangeLog.ActorType.SYSTEM,
    )
    return diagnostic


def register_view(diagnostic: WebAppDiagnostic) -> WebAppDiagnostic:
    """Increment view_count and refresh last_viewed_at."""
    WebAppDiagnostic.objects.filter(pk=diagnostic.pk).update(
        view_count=F('view_count') + 1,
        last_viewed_at=timezone.now(),
    )
    diagnostic.refresh_from_db(fields=['view_count', 'last_viewed_at'])
    return diagnostic


def log_change(
    diagnostic: WebAppDiagnostic,
    *,
    change_type: str,
    description: str = '',
    field_name: str = '',
    old_value: str = '',
    new_value: str = '',
    actor_type: str = '',
) -> DiagnosticChangeLog:
    """Append a DiagnosticChangeLog entry for this diagnostic."""
    return DiagnosticChangeLog.objects.create(
        diagnostic=diagnostic,
        change_type=change_type,
        description=description or '',
        field_name=field_name or '',
        old_value=str(old_value or ''),
        new_value=str(new_value or ''),
        actor_type=actor_type or '',
    )


PUBLIC_VISIBLE_STATUSES = frozenset({
    WebAppDiagnostic.Status.SENT,
    WebAppDiagnostic.Status.VIEWED,
    WebAppDiagnostic.Status.NEGOTIATING,
    WebAppDiagnostic.Status.ACCEPTED,
    WebAppDiagnostic.Status.REJECTED,
})


def visible_sections(diagnostic: WebAppDiagnostic):
    """Return sections to expose on the public client view."""
    if diagnostic.status not in PUBLIC_VISIBLE_STATUSES:
        return []
    sections = sorted(
        diagnostic.sections.filter(is_enabled=True),
        key=lambda s: s.order,
    )
    phase = 'final' if diagnostic.final_sent_at else 'initial'
    allowed = {phase, 'both'}
    return [s for s in sections if s.visibility in allowed]

"""Service layer for the WebAppDiagnostic feature."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from accounts.services.proposal_client_service import build_client_display_name
from content.models import DiagnosticDocument, WebAppDiagnostic
from content.utils import format_cop_email


TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / 'templates' / 'diagnostics'
)

# doc_type → (filename pattern, default title, order)
DOC_TEMPLATES = {
    DiagnosticDocument.DocType.INITIAL_PROPOSAL: (
        'initial_proposal_{lang}.md',
        'Propuesta de Diagnóstico',
        1,
    ),
    DiagnosticDocument.DocType.TECHNICAL_PROPOSAL: (
        'technical_proposal_{lang}.md',
        'Propuesta de Diagnóstico Técnico',
        2,
    ),
    DiagnosticDocument.DocType.SIZING_ANNEX: (
        'sizing_annex_{lang}.md',
        'Anexo de Dimensionamiento Preliminar',
        3,
    ),
}

PLACEHOLDER = '_por definir_'

# Variables that must be filled by the human; empty → render PLACEHOLDER
# instead of an empty string so the document still reads sensibly.
PLACEHOLDER_KEYS = frozenset({
    'investment_amount',
    'duration_label',
    'payment_initial_pct',
    'payment_final_pct',
    'size_category_label',
})

_VAR_RE = re.compile(r'\{\{\s*([a-zA-Z0-9_]+)\s*\}\}')


@lru_cache(maxsize=12)
def _load_template(doc_type: str, language: str) -> str:
    pattern, _title, _order = DOC_TEMPLATES[doc_type]
    try:
        return (TEMPLATES_DIR / pattern.format(lang=language)).read_text(encoding='utf-8')
    except FileNotFoundError:
        return (TEMPLATES_DIR / pattern.format(lang='es')).read_text(encoding='utf-8')


def _classify_size(value: int, thresholds: tuple[int, int]) -> str:
    """Return 'Pequeña' | 'Mediana' | 'Grande' for a numeric metric."""
    low, high = thresholds
    if value <= 0:
        return ''
    if value < low:
        return 'Pequeña'
    if value <= high:
        return 'Mediana'
    return 'Grande'


def build_render_context(diagnostic: WebAppDiagnostic) -> dict:
    """Build the variable map used to substitute `{{vars}}` in templates."""
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


def render_document(doc: DiagnosticDocument, context: dict | None = None) -> str:
    """Substitute `{{var}}` in `doc.content_md` with diagnostic data.

    `context` may be passed in to avoid rebuilding it across multiple docs of
    the same diagnostic in a single response.
    """
    ctx = context if context is not None else build_render_context(doc.diagnostic)

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        value = ctx.get(key)
        if value is None or value == '':
            return PLACEHOLDER if key in PLACEHOLDER_KEYS else ''
        return str(value)

    return _VAR_RE.sub(_replace, doc.content_md)


@transaction.atomic
def create_diagnostic(
    *,
    client,
    language: str = 'es',
    title: str = '',
    created_by=None,
) -> WebAppDiagnostic:
    """Create a diagnostic and load the 3 documents from markdown templates."""
    if not title:
        title = f'Diagnóstico — {build_client_display_name(client)}'

    diagnostic = WebAppDiagnostic.objects.create(
        client=client,
        language=language,
        title=title,
        created_by=created_by,
    )

    for doc_type, (_pattern, default_title, order) in DOC_TEMPLATES.items():
        DiagnosticDocument.objects.create(
            diagnostic=diagnostic,
            doc_type=doc_type,
            title=default_title,
            content_md=_load_template(doc_type, language),
            order=order,
        )

    return diagnostic


def restore_document_from_template(doc: DiagnosticDocument) -> DiagnosticDocument:
    """Reload a document's `content_md` from its source markdown template."""
    doc.content_md = _load_template(doc.doc_type, doc.diagnostic.language)
    doc.is_ready = False
    doc.save(update_fields=['content_md', 'is_ready', 'updated_at'])
    return doc


def transition_status(
    diagnostic: WebAppDiagnostic,
    new_status: str,
) -> WebAppDiagnostic:
    """Validate transition + stamp the matching timestamp.

    Raises ValueError when the transition is not allowed.
    """
    if not diagnostic.can_transition_to(new_status):
        raise ValueError(
            f'invalid_transition: {diagnostic.status} → {new_status}'
        )

    update_fields = ['status', 'updated_at']
    diagnostic.status = new_status
    now = timezone.now()

    # SENT is re-used for both the initial send and the final send. We
    # distinguish them via the timestamp fields: the first transition to
    # SENT stamps `initial_sent_at`; a later return to SENT from NEGOTIATING
    # stamps `final_sent_at`.
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
    return diagnostic


def register_view(diagnostic: WebAppDiagnostic) -> WebAppDiagnostic:
    """Increment view_count and refresh last_viewed_at."""
    WebAppDiagnostic.objects.filter(pk=diagnostic.pk).update(
        view_count=F('view_count') + 1,
        last_viewed_at=timezone.now(),
    )
    diagnostic.refresh_from_db(fields=['view_count', 'last_viewed_at'])
    return diagnostic


PUBLIC_VISIBLE_STATUSES = frozenset({
    WebAppDiagnostic.Status.SENT,
    WebAppDiagnostic.Status.VIEWED,
    WebAppDiagnostic.Status.NEGOTIATING,
    WebAppDiagnostic.Status.ACCEPTED,
    WebAppDiagnostic.Status.REJECTED,
})


def visible_documents(diagnostic: WebAppDiagnostic):
    """Return the documents visible to the public client given the status.

    Filters in Python so a prefetched `documents` cache is not invalidated.
    The initial-vs-final send distinction now lives in the timestamps rather
    than the status enum, so we gate on `final_sent_at`.
    """
    docs = sorted(diagnostic.documents.all(), key=lambda d: d.order)
    if diagnostic.status not in PUBLIC_VISIBLE_STATUSES:
        return []
    if diagnostic.final_sent_at is None:
        return [d for d in docs if d.doc_type == DiagnosticDocument.DocType.INITIAL_PROPOSAL]
    ready = [d for d in docs if d.is_ready]
    return ready or docs

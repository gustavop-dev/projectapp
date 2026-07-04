"""
Tool registry for the Clients MCP connector.

Lets claude.ai manage proposal clients (the ``/panel/clients`` page): search,
list, inspect, create, update and delete client profiles. Clients are
``accounts.UserProfile`` rows with role=client; they are the canonical identity
shared by proposals and diagnostics.

Guardrails baked in (mirror the panel exactly, by delegating to the same
service):
- Writes always go through ``proposal_client_service`` (never a bare
  ``serializer.save()``) so proposal snapshots stay in sync and email-in-use
  conflicts are enforced.
- Delete only succeeds for true orphans (0 proposals, 0 projects, 0
  diagnostics); otherwise the exact ``client_has_*:N`` reason is surfaced.

Each entry: {'name', 'description', 'input_schema', 'handler'}. Handlers take
the raw ``arguments`` dict, return a JSON-serializable dict, and raise
ToolError for business errors.
"""
from accounts.models import UserProfile
from accounts.serializers import ProjectListSerializer
from accounts.services import proposal_client_service
from content.mcp.protocol import ToolError
from content.serializers.diagnostic import DiagnosticListSerializer
from content.serializers.proposal import ProposalListSerializer
from content.serializers.proposal_clients import (
    ProposalClientSearchSerializer,
    ProposalClientSerializer,
)
# Reuse the panel view's annotated queryset + helpers so the MCP exposes the
# exact same computed fields (counts, last_status, is_orphan) as /panel/clients.
from content.views.proposal_clients import _base_queryset, _get_profile_or_404


def _get_client_or_error(client_id):
    profile = _get_profile_or_error_none(client_id)
    if profile is None:
        raise ToolError(
            f'No existe un cliente con id={client_id}. '
            'Usa search_clients o list_clients para ver los disponibles.'
        )
    return profile


def _get_profile_or_error_none(client_id):
    try:
        return _get_profile_or_404(int(client_id))
    except (TypeError, ValueError):
        return None


# ── Handlers ─────────────────────────────────────────────────────────────────

def search_clients(arguments):
    query = (arguments.get('q') or '').strip()
    qs = UserProfile.objects.clients()
    if query:
        from django.db.models import Q
        qs = qs.filter(
            Q(user__email__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(company_name__icontains=query)
        )
    qs = qs.order_by('-updated_at')[:20]
    return {'results': ProposalClientSearchSerializer(qs, many=True).data}


def list_clients(arguments):
    from django.db.models import Q
    qs = _base_queryset()

    search = (arguments.get('search') or '').strip()
    if search:
        qs = qs.filter(
            Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(company_name__icontains=search)
        )

    orphans = arguments.get('orphans')
    if orphans is True:
        qs = qs.filter(proposals_count=0, projects_count=0)
    elif orphans is False:
        qs = qs.exclude(proposals_count=0, projects_count=0)

    try:
        limit = min(int(arguments.get('limit', 100) or 100), 500)
    except (TypeError, ValueError):
        raise ToolError('limit debe ser un entero.')

    qs = qs.prefetch_related('proposals').order_by('-last_proposal_at', '-updated_at')[:limit]
    results = ProposalClientSerializer(qs, many=True).data
    return {'count': len(results), 'results': results}


def get_client(arguments):
    profile = _get_client_or_error(arguments.get('client_id'))
    payload = ProposalClientSerializer(profile).data
    proposals = profile.proposals.select_related('client__user').order_by('-created_at')
    payload['proposals'] = ProposalListSerializer(proposals, many=True).data
    projects = profile.user.projects.select_related('client__profile').order_by('-created_at')
    payload['projects'] = ProjectListSerializer(projects, many=True).data
    diagnostics = profile.web_app_diagnostics.select_related('client__user').order_by('-created_at')
    payload['diagnostics'] = DiagnosticListSerializer(diagnostics, many=True).data
    return payload


def create_client(arguments):
    name = (arguments.get('name') or '').strip()
    email = (arguments.get('email') or '').strip()
    phone = (arguments.get('phone') or '').strip()
    company = (arguments.get('company') or '').strip()

    if not name and not email and not company:
        raise ToolError('Debes proporcionar al menos un nombre, email o empresa.')

    try:
        profile = proposal_client_service.get_or_create_client_for_proposal(
            name=name, email=email, phone=phone, company=company,
        )
    except ValueError as exc:
        raise ToolError(f'Datos de cliente inválidos: {exc}')

    return ProposalClientSerializer(_get_profile_or_404(profile.pk)).data


def update_client(arguments):
    profile = _get_client_or_error(arguments.get('client_id'))

    payload = {}
    for key in ('name', 'email', 'phone', 'company'):
        if key in arguments:
            payload[key] = arguments[key]

    if not payload:
        raise ToolError(
            'No se indicó ningún campo para actualizar. Envía al menos uno de: '
            'name, email, phone, company.'
        )

    try:
        proposal_client_service.update_client_profile(profile, **payload)
    except ValueError as exc:
        raise ToolError(f'No se pudo actualizar el cliente: {exc}')

    return ProposalClientSerializer(_get_profile_or_404(profile.pk)).data


def delete_client(arguments):
    profile = _get_client_or_error(arguments.get('client_id'))
    profile_id = profile.pk
    try:
        proposal_client_service.delete_orphan_client(profile)
    except ValueError as exc:
        # Service raises 'client_has_proposals:N' / 'client_has_projects:N' /
        # 'client_has_diagnostics:N'. Preserve the exact reason for the model.
        raise ToolError(
            f'No se puede eliminar: el cliente aún tiene referencias ({exc}). '
            'Elimina o reasigna esas propuestas/proyectos/diagnósticos primero.'
        )
    return {'deleted': True, 'id': profile_id}


# ── Registry ─────────────────────────────────────────────────────────────────

_CLIENT_ID_PROP = {
    'client_id': {'type': 'integer', 'description': 'ID del perfil de cliente.'},
}

CLIENT_TOOLS = [
    {
        'name': 'search_clients',
        'description': (
            'Autocompletado rápido de clientes. Busca por email, nombre o '
            'empresa (parcial) y devuelve hasta 20 resultados resumidos. '
            'Úsalo para encontrar el client_id que necesitan otras tools '
            '(p. ej. crear una propuesta o un diagnóstico).'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'q': {'type': 'string', 'description': 'Texto a buscar (parcial).'},
            },
        },
        'handler': search_clients,
    },
    {
        'name': 'list_clients',
        'description': (
            'Lista clientes con métricas (nº de propuestas, proyectos, '
            'diagnósticos, último estado, si es huérfano). Filtros: search '
            '(texto), orphans (true=sólo sin propuestas ni proyectos, '
            'false=el resto), limit (default 100, máx 500).'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'search': {'type': 'string'},
                'orphans': {'type': 'boolean'},
                'limit': {'type': 'integer', 'default': 100, 'maximum': 500},
            },
        },
        'handler': list_clients,
    },
    {
        'name': 'get_client',
        'description': (
            'Devuelve un cliente con sus propuestas, proyectos de plataforma y '
            'diagnósticos anidados.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': _CLIENT_ID_PROP,
            'required': ['client_id'],
        },
        'handler': get_client,
    },
    {
        'name': 'create_client',
        'description': (
            'Crea un cliente nuevo (sin propuesta ni email de invitación). '
            'Requiere al menos uno de name/email/company. Si omites el email se '
            'genera un placeholder. No reutiliza cuentas de administrador.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'phone': {'type': 'string'},
                'company': {'type': 'string'},
            },
        },
        'handler': create_client,
    },
    {
        'name': 'update_client',
        'description': (
            'Actualiza un cliente (parcial) y propaga el cambio a todas sus '
            'propuestas. Envía client_id y al menos uno de: name, email, '
            'phone, company. Falla si el email ya está en uso por otro cliente.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                **_CLIENT_ID_PROP,
                'name': {'type': 'string'},
                'email': {'type': 'string'},
                'phone': {'type': 'string'},
                'company': {'type': 'string'},
            },
            'required': ['client_id'],
        },
        'handler': update_client,
    },
    {
        'name': 'delete_client',
        'description': (
            'Elimina un cliente SÓLO si es huérfano (0 propuestas, 0 proyectos, '
            '0 diagnósticos). Si tiene referencias, la operación falla '
            'indicando cuántas.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': _CLIENT_ID_PROP,
            'required': ['client_id'],
        },
        'handler': delete_client,
    },
]

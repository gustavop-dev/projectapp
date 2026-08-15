"""
Code-level defaults for ``SavedFilterTab``, keyed by view.

Each entry is ``{'name': str, 'filters': dict}``. The ``filters`` dict must
match the frontend ``DEFAULT_FILTERS`` shape for its view:

- ``client``   -> ``frontend/composables/useClientFilters.js`` (lastStatuses,
  projectTypes, marketTypes, totalProposalsMin/Max, acceptedMin/Max,
  lastActivityAfter/Before)
- ``proposal`` -> ``frontend/composables/useProposalFilters.js`` (statuses,
  projectTypes, marketTypes, currencies, languages, investmentMin/Max,
  heatScoreMin/Max, viewCountMin/Max, createdAfter/Before,
  lastActivityAfter/Before, isActive, technicalViewed)

Partial dicts are fine: the frontend merges stored filters over its own
fresh defaults, so only the keys that differ need to be listed here.

- ``accounting_*`` -> each page's ``useAccountingFilters`` defaults in
  ``frontend/pages/panel/accounting/*.vue`` (bool tabs use the strings
  ``'true'``/``'false'`` expected by ``matchBoolean``).
- ``view_map``  -> ``frontend/composables/useViewMapFilters.js`` (categories,
  audiences, viewTypes).

Values captured from the production DB on 2026-07-09 (one tab per proposal
status, mirrored across the client and proposal views). Re-seed with
``python manage.py seed_filter_tabs``.
"""

DEFAULT_FILTER_TABS = {
    'client': [
        {'name': 'Draft', 'filters': {'lastStatuses': ['draft']}},
        {'name': 'Sent/Viewed', 'filters': {'lastStatuses': ['sent', 'viewed']}},
        {'name': 'Negociación', 'filters': {'lastStatuses': ['negotiating']}},
        {'name': 'Accepted', 'filters': {'lastStatuses': ['accepted']}},
        {'name': 'Expired', 'filters': {'lastStatuses': ['expired']}},
        {'name': 'Rejected', 'filters': {'lastStatuses': ['rejected']}},
        {'name': 'Finished', 'filters': {'lastStatuses': ['finished']}},
    ],
    'proposal': [
        {'name': 'Draft', 'filters': {'statuses': ['draft']}},
        {'name': 'Sent/Viewed', 'filters': {'statuses': ['sent', 'viewed']}},
        {'name': 'Negociación', 'filters': {'statuses': ['negotiating']}},
        {'name': 'Accepted', 'filters': {'statuses': ['accepted']}},
        {'name': 'Expired', 'filters': {'statuses': ['expired']}},
        {'name': 'Rejected', 'filters': {'statuses': ['rejected']}},
        {'name': 'Finished', 'filters': {'statuses': ['finished']}},
    ],
    'accounting_income': [
        # "Todos los esperados" keeps every expected record (paid, partial and
        # untouched). The uncollected-only cut ("Solo esperados") and its
        # hosting variant are builtin tabs in incomes.vue instead: the landing
        # tab must not be silently rewritten when a filter is tweaked.
        {'name': 'Todos los esperados', 'filters': {'kind': 'expected'}},
        {'name': 'Líquidos', 'filters': {'kind': 'liquid'}},
        {'name': 'Gustavo', 'filters': {'partner': 'gustavo'}},
        {'name': 'Carlos', 'filters': {'partner': 'carlos'}},
        {'name': 'ProjectApp', 'filters': {'partner': 'projectapp'}},
    ],
    'accounting_expense': [
        {'name': 'Negocio', 'filters': {'categories': ['business']}},
        {'name': 'Personales', 'filters': {'categories': ['personal']}},
        {'name': 'Empresa', 'filters': {'ledger': 'company'}},
        {'name': 'Personal Gustavo', 'filters': {'ledger': 'gustavo'}},
        {'name': 'Personal Carlos', 'filters': {'ledger': 'carlos'}},
    ],
    'accounting_hosting': [
        {'name': 'Activos', 'filters': {'isActive': 'true'}},
        {'name': 'Inactivos', 'filters': {'isActive': 'false'}},
        {'name': 'Mensuales', 'filters': {'modalities': ['monthly']}},
        {'name': 'Anuales', 'filters': {'modalities': ['annual']}},
    ],
    'accounting_pocket': [
        {'name': 'Entradas', 'filters': {'direction': 'in'}},
        {'name': 'Salidas', 'filters': {'direction': 'out'}},
    ],
    'accounting_recurring': [
        {'name': 'Activos', 'filters': {'is_active': 'true'}},
        {'name': 'Mensuales', 'filters': {'frequency': ['monthly'], 'is_active': 'true'}},
        {'name': 'Anuales', 'filters': {'frequency': ['annual'], 'is_active': 'true'}},
        {'name': 'USD', 'filters': {'currency': 'USD'}},
        {'name': 'Variables', 'filters': {'cost_type': 'variable'}},
    ],
    'view_map': [
        {'name': 'Admin', 'filters': {'audiences': ['admin']}},
        {'name': 'Público', 'filters': {'audiences': ['public']}},
        {'name': 'Cliente', 'filters': {'audiences': ['client']}},
        {'name': 'Dashboards', 'filters': {'viewTypes': ['dashboard']}},
        {'name': 'Configuración', 'filters': {'viewTypes': ['config']}},
    ],
    'accounting_ads': [
        {'name': 'Facebook', 'filters': {'platform': ['facebook']}},
        {'name': 'Google', 'filters': {'platform': ['google']}},
        {'name': 'Otros', 'filters': {'platform': ['other']}},
    ],
    # Historial. The date cuts ("Hoy", "Últimos 7 días") are builtin tabs in
    # history.vue instead: a stored `date_from` would freeze on the day it was
    # seeded, and a tab called "Hoy" that means last Tuesday is a lie.
    'accounting_history_sends': [
        # Second on purpose: it is the first place anyone lands when someone
        # says a notice never arrived.
        {'name': 'Fallidos', 'filters': {'status': ['failed']}},
        {
            'name': 'Recordatorios de cobro',
            'filters': {'template_key': [
                'accounting_payment_calendar', 'collection_account_sent',
            ]},
        },
        {
            'name': 'Cambios contables',
            'filters': {'template_key': ['accounting_change']},
        },
        {'name': 'Eliminaciones', 'filters': {'origin_action': ['deleted']}},
    ],
    'accounting_history_changes': [
        {'name': 'Eliminaciones', 'filters': {'action': ['deleted']}},
        {'name': 'Ingresos', 'filters': {'entity_type': ['income']}},
        {'name': 'Gastos', 'filters': {'entity_type': ['expense']}},
        {'name': 'Hostings', 'filters': {'entity_type': ['hosting']}},
    ],
}

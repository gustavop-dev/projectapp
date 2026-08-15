"""
Code-level defaults for ``SavedFilterTab``, keyed by view.

Each entry is ``{'name': str, 'filters': dict}``. The ``filters`` dict must
match the frontend ``DEFAULT_FILTERS`` shape for its view:

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
status). Re-seed with ``python manage.py seed_filter_tabs``.

``client`` has no entry on purpose: its proposal-status cuts are code-level
subfilters of the Propuestas module (``frontend/constants/clientFilters.js``),
not seeded rows. Migration ``0047`` dropped the ones already in the database.
"""

DEFAULT_FILTER_TABS = {
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
    # Historial. Three of its presets are builtin tabs in history.vue instead
    # of rows here: "Hoy" and "Últimos 7 días" because a stored `date_from`
    # would freeze on the day it was seeded — a tab called "Hoy" that means
    # last Tuesday is a lie — and "Fallidos" because it has to sit second in
    # the strip (it is where anyone lands when a notice did not arrive) and
    # builtins render before the saved ones. The three seeded here are the
    # opinionated groupings, which is what "Restablecer" exists to put back.
    'accounting_history_sends': [
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

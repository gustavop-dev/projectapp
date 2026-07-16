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
        {'name': 'Esperados', 'filters': {'kind': 'expected'}},
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
}

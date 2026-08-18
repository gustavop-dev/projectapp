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
not seeded rows. Migration ``0049`` dropped the ones already in the database.
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
    # The three attribution cuts are the consulta that repeats ("what came out
    # of Gustavo's pocket"); "Sin vincular" is the repair queue: movements that
    # never got their mirror in Ingresos or Gastos.
    'accounting_pocket': [
        {'name': 'Entradas', 'filters': {'direction': 'in'}},
        {'name': 'Salidas', 'filters': {'direction': 'out'}},
        {'name': 'Gustavo', 'filters': {'attribution': ['gustavo']}},
        {'name': 'Carlos', 'filters': {'attribution': ['carlos']}},
        {'name': 'Empresa', 'filters': {'attribution': ['company']}},
        {'name': 'Sin vincular', 'filters': {'linked': 'false'}},
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


# Builtin quick-filters: the ones the frontend defines in code and this file
# deliberately does NOT seed (see the comments above about "Solo esperados",
# "Hoy" and "Últimos 7 días"). Only `key` and `name` are listed — no filters,
# ever. The definition stays in the frontend constant the key matches; what
# the backend keeps is a placeholder row per (user, view, key) whose only job
# is to carry the user's `order` and `is_hidden`, so a builtin can be dragged
# and hidden alongside the saved tabs instead of being nailed to the front.
#
# The order here is the factory order — what "Restablecer" puts back — and it
# must match the order of each page's `builtinTabs` array. The keys must match
# their `id`s. Sources:
#
#   accounting_income          frontend/pages/panel/accounting/incomes.vue
#   accounting_hosting         frontend/pages/panel/accounting/hostings.vue
#   accounting_collections     frontend/pages/panel/accounting/collections.vue
#   accounting_history_*       frontend/constants/historyFilters.js
#   client                     frontend/constants/clientFilters.js (CLIENT_SUBFILTERS)
#
# Drift degrades gracefully in both directions: a placeholder with no matching
# constant is dropped from the strip, and a constant with no placeholder keeps
# its code position and simply cannot be dragged. Quiet, so
# `test_builtin_registry_keys_exist_in_the_frontend_sources` pins the keys to
# the frontend files listed above.
BUILTIN_FILTER_TABS = {
    'accounting_income': [
        {'key': 'expected-pending', 'name': 'Solo esperados'},
        {'key': 'hosting-expected', 'name': 'Hosting esperados'},
        {'key': 'lost', 'name': 'Perdidos'},
        {'key': 'no-client', 'name': 'Sin cliente'},
        {'key': 'no-project', 'name': 'Sin proyecto'},
    ],
    'accounting_hosting': [
        {'key': 'no-client', 'name': 'Sin cliente'},
        {'key': 'no-project', 'name': 'Sin proyecto'},
    ],
    'accounting_collections': [
        {'key': 'open', 'name': 'Por cobrar'},
        {'key': 'overdue', 'name': 'Vencidas'},
        {'key': 'no-project', 'name': 'Sin proyecto'},
    ],
    'accounting_history_sends': [
        {'key': 'failed', 'name': 'Fallidos'},
        {'key': 'today', 'name': 'Hoy'},
        {'key': 'last7', 'name': 'Últimos 7 días'},
    ],
    'accounting_history_changes': [
        {'key': 'today', 'name': 'Hoy'},
        {'key': 'last7', 'name': 'Últimos 7 días'},
    ],
    # Grouped by module, in the same order as CLIENT_SUBFILTERS: the strip
    # only ever shows one module at a time, so the position that matters is
    # the one within its group.
    'client': [
        {'key': 'status-draft', 'name': 'Draft'},
        {'key': 'status-sent-viewed', 'name': 'Sent/Viewed'},
        {'key': 'status-negotiating', 'name': 'Negociación'},
        {'key': 'status-accepted', 'name': 'Accepted'},
        {'key': 'status-expired', 'name': 'Expired'},
        {'key': 'status-rejected', 'name': 'Rejected'},
        {'key': 'status-finished', 'name': 'Finished'},
        {'key': 'diagnostic-billed', 'name': 'Con diagnóstico facturado'},
        {'key': 'no-diagnostic', 'name': 'Sin diagnóstico'},
        {'key': 'diagnostic-unconverted', 'name': 'Diagnóstico sin propuesta posterior'},
        {'key': 'active-project', 'name': 'Con proyecto activo'},
        {'key': 'no-project', 'name': 'Sin proyecto'},
        {'key': 'hosting-charged', 'name': 'Con hosting cobrado'},
        {'key': 'hosting-any', 'name': 'Con hosting (histórico)'},
        {'key': 'no-hosting', 'name': 'Sin hosting'},
        {'key': 'no-billing', 'name': 'Sin datos de facturación'},
        {'key': 'docs-with', 'name': 'Con documentos'},
        {'key': 'docs-none', 'name': 'Sin documentos'},
        {'key': 'docs-no-project', 'name': 'Con documentos sin proyecto'},
        {'key': 'docs-with-folder', 'name': 'Con carpeta'},
        {'key': 'emails-any', 'name': 'Con correos enviados'},
        {'key': 'no-emails', 'name': 'Sin ningún correo'},
        {'key': 'emails-failed', 'name': 'Con envíos fallidos'},
        {'key': 'emails-cold', 'name': 'Sin contacto en los últimos 30 días'},
    ],
}

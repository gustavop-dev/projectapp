/**
 * The whole filter definition for /panel/clients: the predefined one-click
 * filters plus the `useAccountingFilters` configuration the page runs on.
 *
 * It lives here as plain data so the page and its tests share one definition
 * instead of drifting apart. The mechanism itself is `useAccountingFilters`
 * (this view used to run on `useClientFilters`, its pre-generalization
 * ancestor, which never gained builtin tabs).
 *
 * Each preset becomes a builtin tab: selecting one writes its id into
 * `currentFilters.preset`, and the `preset` matcher below runs the matching
 * predicate over the loaded rows. Adding another shortcut is one entry in
 * CLIENT_PRESETS — no new plumbing in the page, the panel or the composable.
 *
 * Predicates may only read fields the clients list endpoint already returns
 * (see ProposalClientSerializer): the filtering happens in the browser over
 * the rows the server sent, like every other filter on this page.
 */

import {
  matchDateRange,
  matchIncludes,
  matchNumberRange,
} from '~/composables/useAccountingFilters';

/**
 * Billing identity is stored inconsistently by design: `billing_code` is a
 * unique column that holds NULL when unset, while `nit` and `cedula` default
 * to ''. Both shapes mean "missing".
 */
function isBlank(value) {
  return !String(value ?? '').trim();
}

export const CLIENT_PRESETS = [
  {
    id: 'hosting-charged',
    name: 'Con hosting cobrado',
    // "Cobrado" is the same `is_active` the hosting rows already render as
    // "Vigente", so this cut reconciles with what the Hostings tab shows.
    match: (client) => Number(client.active_hostings_count || 0) > 0,
  },
  {
    id: 'hosting-any',
    name: 'Con hosting (histórico)',
    match: (client) => Number(client.hostings_count || 0) > 0,
  },
  {
    id: 'no-billing',
    name: 'Sin datos de facturación',
    match: (client) =>
      isBlank(client.nit) && isBlank(client.cedula) && isBlank(client.billing_code),
  },
  {
    id: 'active-project',
    name: 'Con proyecto activo',
    // `projects_count` counts every status, so it would let an
    // archived-only client through; this reads the active-only aggregate.
    match: (client) => Number(client.active_projects_count || 0) > 0,
  },
];

export const CLIENT_PRESET_IDS = CLIENT_PRESETS.map((preset) => preset.id);

const PRESET_BY_ID = new Map(CLIENT_PRESETS.map((preset) => [preset.id, preset]));

export function findClientPreset(id) {
  return PRESET_BY_ID.get(String(id ?? '')) || null;
}

/**
 * `useAccountingFilters` matcher. The active preset id lives in a single
 * `preset` filter key, so only one shortcut can be on at a time — which is
 * exactly what a tab bar models.
 */
export function matchClientPreset(record, _value, filters) {
  const preset = findClientPreset(filters.preset);
  return preset ? preset.match(record) : true;
}
matchClientPreset.keys = ['preset'];

/** Presets that make the per-row hosting count worth showing. */
export const HOSTING_PRESET_IDS = ['hosting-charged', 'hosting-any'];

/**
 * Options for `useAccountingFilters`.
 *
 * `searchFields` is deliberately empty: this page's search box is server-side
 * (it refetches with ?search= across the whole table, not just the loaded
 * rows), so `currentFilters.search` stays inert and selecting a preset — which
 * resets the filters to their defaults — can never wipe what the user typed.
 *
 * `viewName` stays 'client', so the ?clientTab= URL param, the
 * useSavedFilterTabs('client') key and the seeded saved tabs all keep working.
 */
export const CLIENT_FILTERS_CONFIG = {
  viewName: 'client',
  searchFields: [],
  defaultTabId: 'all',
  defaults: {
    lastStatuses: [],
    projectTypes: [],
    marketTypes: [],
    totalProposalsMin: null,
    totalProposalsMax: null,
    acceptedMin: null,
    acceptedMax: null,
    lastActivityAfter: null,
    lastActivityBefore: null,
    preset: '',
  },
  matchers: {
    lastStatuses: matchIncludes('last_status', 'lastStatuses'),
    projectTypes: matchIncludes('project_types', 'projectTypes'),
    marketTypes: matchIncludes('market_types', 'marketTypes'),
    totalProposals: matchNumberRange(
      'total_proposals', 'totalProposalsMin', 'totalProposalsMax',
    ),
    accepted: matchNumberRange('accepted_count', 'acceptedMin', 'acceptedMax'),
    activityRange: matchDateRange(
      'last_sent_at', 'lastActivityAfter', 'lastActivityBefore',
    ),
    preset: matchClientPreset,
  },
  builtinTabs: CLIENT_PRESETS.map(({ id, name }) => ({
    id, name, filters: { preset: id },
  })),
};

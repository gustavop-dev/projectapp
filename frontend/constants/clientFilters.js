/**
 * The whole filter definition for /panel/clients: the business modules, the
 * subfilters each one offers, and the `useAccountingFilters` configuration the
 * page runs on.
 *
 * It lives here as plain data so the page and its tests share one definition
 * instead of drifting apart. The mechanism itself is `useAccountingFilters`.
 *
 * The view is read along three independent axes:
 *
 *   - Client status (Activos / Huérfanos / Inactivos) — cross-cutting, applied
 *     server-side by the page itself. It is not part of this file.
 *   - Module (level 1) — `module`. It does NOT narrow the list: it decides
 *     which subfilters level 2 offers. That is what lets a module host both a
 *     cut and its complement ("Con hosting cobrado" and "Sin hosting").
 *   - Subfilter (level 2) — the cut itself.
 *
 * Subfilters are expressed as values of the filter panel's own controls, never
 * as opaque predicates. That is deliberate: it is what makes every predefined
 * filter reproducible from the panel, removable by its chip and saveable as a
 * named tab, all through the machinery that already exists. Adding one is a
 * single entry in CLIENT_SUBFILTERS plus, if it needs a new control, a matcher
 * and its widget in ClientFilterPanel.
 *
 * Matchers may only read fields the clients list endpoint already returns (see
 * ProposalClientSerializer): the filtering happens in the browser over the rows
 * the server sent, like every other filter on this page.
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

// ---------------------------------------------------------------------------
// Level 1: business modules
// ---------------------------------------------------------------------------

export const CLIENT_MODULE_ALL = 'all';

export const CLIENT_MODULES = [
  { id: CLIENT_MODULE_ALL, name: 'Todos' },
  { id: 'proposals', name: 'Propuestas' },
  { id: 'projects', name: 'Proyectos' },
  // Hosting is its own module rather than a corner of Contabilidad: it is a
  // service line with a life of its own, and its subfilters grow once hosting
  // records its period (PA-51).
  { id: 'hosting', name: 'Hosting' },
  { id: 'accounting', name: 'Contabilidad' },
];

const MODULE_BY_ID = new Map(CLIENT_MODULES.map((m) => [m.id, m]));

export function findClientModule(id) {
  return MODULE_BY_ID.get(String(id ?? '')) || null;
}

export function clientModuleName(id) {
  return findClientModule(id)?.name || '';
}

// ---------------------------------------------------------------------------
// Level 2: subfilters, grouped by module
// ---------------------------------------------------------------------------

/**
 * Ids are part of the URL (`?clientTab=`), so the four that shipped with the
 * predefined filters keep the names they had — old links stay valid.
 */
export const CLIENT_SUBFILTERS = [
  // Propuestas — the commercial cycle. These were seeded saved tabs until
  // migration 0049; as code-level entries they count uniformly, cannot be
  // deleted by accident and no longer eat 7 of the 12 saved-tab slots.
  { id: 'status-draft', name: 'Draft', module: 'proposals', filters: { lastStatuses: ['draft'] } },
  { id: 'status-sent-viewed', name: 'Sent/Viewed', module: 'proposals', filters: { lastStatuses: ['sent', 'viewed'] } },
  { id: 'status-negotiating', name: 'Negociación', module: 'proposals', filters: { lastStatuses: ['negotiating'] } },
  { id: 'status-accepted', name: 'Accepted', module: 'proposals', filters: { lastStatuses: ['accepted'] } },
  { id: 'status-expired', name: 'Expired', module: 'proposals', filters: { lastStatuses: ['expired'] } },
  { id: 'status-rejected', name: 'Rejected', module: 'proposals', filters: { lastStatuses: ['rejected'] } },
  { id: 'status-finished', name: 'Finished', module: 'proposals', filters: { lastStatuses: ['finished'] } },

  // Proyectos — leans on the Plataforma module (PA-49), where a project
  // becomes an administrable entity.
  { id: 'active-project', name: 'Con proyecto activo', module: 'projects', filters: { projectStatus: 'active' } },
  { id: 'no-project', name: 'Sin proyecto', module: 'projects', filters: { projectStatus: 'none' } },

  // Hosting
  { id: 'hosting-charged', name: 'Con hosting cobrado', module: 'hosting', filters: { hostingStatus: 'charged' } },
  { id: 'hosting-any', name: 'Con hosting (histórico)', module: 'hosting', filters: { hostingStatus: 'any' } },
  { id: 'no-hosting', name: 'Sin hosting', module: 'hosting', filters: { hostingStatus: 'none' } },

  // Contabilidad — the smallest module today and the one that will grow most
  // (cuentas de cobro pendientes/vencidas land here).
  { id: 'no-billing', name: 'Sin datos de facturación', module: 'accounting', filters: { billingData: 'missing' } },
];

const SUBFILTER_BY_ID = new Map(CLIENT_SUBFILTERS.map((s) => [s.id, s]));

export function findClientSubfilter(id) {
  return SUBFILTER_BY_ID.get(String(id ?? '')) || null;
}

export function clientSubfiltersFor(moduleId) {
  return CLIENT_SUBFILTERS.filter((s) => s.module === String(moduleId ?? ''));
}

/**
 * Panel options for a module's scalar filter key, derived from the subfilters
 * themselves. Requirement: every predefined filter must also exist as a
 * composable control in the panel — deriving both from one list is what makes
 * that true by construction instead of by discipline.
 */
export function subfilterOptionsFor(moduleId, key) {
  return clientSubfiltersFor(moduleId)
    .filter((s) => typeof s.filters[key] === 'string')
    .map((s) => ({ value: s.filters[key], label: s.name }));
}

/**
 * Whether a row satisfies a subfilter, running only the matchers the subfilter
 * actually sets. Used for the counts each one advertises before being applied,
 * so the badge cannot disagree with what pressing it returns.
 */
export function matchesSubfilter(subfilter, record) {
  return Object.entries(CLIENT_FILTERS_CONFIG.matchers).every(([key, fn]) => {
    const keys = Array.isArray(fn.keys) && fn.keys.length ? fn.keys : [key];
    if (!keys.some((k) => k in subfilter.filters)) return true;
    return fn(record, subfilter.filters[key], subfilter.filters);
  });
}

/** The subfilter a set of filter values corresponds to, if any. */
export function matchingSubfilter(filters) {
  if (!filters) return null;
  return CLIENT_SUBFILTERS.find((sub) =>
    Object.entries(sub.filters).every(([key, value]) => {
      const current = filters[key];
      return Array.isArray(value)
        ? Array.isArray(current)
          && current.length === value.length
          && value.every((v) => current.includes(v))
        : current === value;
    }),
  ) || null;
}

// ---------------------------------------------------------------------------
// Matchers for the module-specific controls
// ---------------------------------------------------------------------------

/**
 * "Cobrado" is `is_active`, the same flag the hosting rows already render as
 * "Vigente" and the Hostings tab labels "Vigentes", so this cut reconciles with
 * what that tab shows. Adding valid_to >= hoy would have invented a third
 * definition neither surface agrees with.
 */
export function matchHostingStatus(record, value) {
  const ever = Number(record.hostings_count || 0);
  if (value === 'charged') return Number(record.active_hostings_count || 0) > 0;
  if (value === 'any') return ever > 0;
  if (value === 'none') return ever === 0;
  return true;
}
matchHostingStatus.keys = ['hostingStatus'];

/**
 * `projects_count` counts every status, so "activo" reads the active-only
 * aggregate while "Sin proyecto" means none at all — the same predicate the
 * endpoint exposes as `without_projects`.
 */
export function matchProjectStatus(record, value) {
  if (value === 'active') return Number(record.active_projects_count || 0) > 0;
  if (value === 'none') return Number(record.projects_count || 0) === 0;
  return true;
}
matchProjectStatus.keys = ['projectStatus'];

export function matchBillingData(record, value) {
  const missing = isBlank(record.nit) && isBlank(record.cedula) && isBlank(record.billing_code);
  if (value === 'missing') return missing;
  if (value === 'complete') return !missing;
  return true;
}
matchBillingData.keys = ['billingData'];

// ---------------------------------------------------------------------------
// Legacy `preset` key
// ---------------------------------------------------------------------------

const LEGACY_PRESET_MAP = {
  'hosting-charged': { hostingStatus: 'charged', module: 'hosting' },
  'hosting-any': { hostingStatus: 'any', module: 'hosting' },
  'no-billing': { billingData: 'missing', module: 'accounting' },
  'active-project': { projectStatus: 'active', module: 'projects' },
};

/**
 * Translate a tab saved while the predefined filters lived in a single `preset`
 * key into the per-module keys that replaced it. Without this such a tab would
 * still load, but silently filter nothing.
 */
export function normalizeLegacyPreset(filters) {
  if (!filters || !filters.preset) return filters;
  const { preset, ...rest } = filters;
  return { ...rest, ...(LEGACY_PRESET_MAP[String(preset)] || {}) };
}

// ---------------------------------------------------------------------------
// useAccountingFilters configuration
// ---------------------------------------------------------------------------

/**
 * `searchFields` is deliberately empty: this page's search box is server-side
 * (it refetches with ?search= across the whole table, not just the loaded
 * rows), so `currentFilters.search` stays inert and selecting a subfilter —
 * which resets the filters to their defaults — can never wipe what the user
 * typed.
 *
 * `viewName` stays 'client', so the ?clientTab= URL param and the
 * useSavedFilterTabs('client') key keep working.
 *
 * `module` is a default but never a matcher: it groups, it does not narrow, so
 * it must not count towards the active-filter badge nor raise a chip. Living
 * inside the filters dict is what lets a saved tab carry its module without a
 * schema change.
 */
export const CLIENT_FILTERS_CONFIG = {
  viewName: 'client',
  searchFields: [],
  defaultTabId: 'all',
  moduleKey: 'module',
  normalizeFilters: normalizeLegacyPreset,
  defaults: {
    module: CLIENT_MODULE_ALL,
    lastStatuses: [],
    projectTypes: [],
    marketTypes: [],
    totalProposalsMin: null,
    totalProposalsMax: null,
    acceptedMin: null,
    acceptedMax: null,
    lastActivityAfter: null,
    lastActivityBefore: null,
    hostingStatus: '',
    projectStatus: '',
    billingData: '',
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
    hostingStatus: matchHostingStatus,
    projectStatus: matchProjectStatus,
    billingData: matchBillingData,
  },
  builtinTabs: CLIENT_SUBFILTERS.map(({ id, name, module, filters }) => ({
    id, name, module, filters: { ...filters, module },
  })),
};

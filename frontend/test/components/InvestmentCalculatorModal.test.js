/**
 * Tests for InvestmentCalculatorModal logic.
 *
 * Covers: module selection, dynamic total calculation,
 * localStorage persistence, formatPrice helper, and
 * initial state from saved selections.
 */

// ── Fixtures ─────────────────────────────────────────────────────────────────

const MODULES_FIXTURE = [
  { id: 'web', name: 'Sitio Web', price: 3000000, included: true },
  { id: 'seo', name: 'SEO', price: 500000, included: false },
  { id: 'analytics', name: 'Analytics', price: 200000, included: true },
];

const PROPOSAL_UUID = 'abc-123-def';
const STORAGE_KEY = `proposal-${PROPOSAL_UUID}-modules`;


// ── formatPrice (extracted logic) ────────────────────────────────────────────

/**
 * Mirrors the formatPrice function from InvestmentCalculatorModal.vue.
 */
function formatPrice(value) {
  if (!value && value !== 0) return '';
  return '$' + Number(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

describe('formatPrice', () => {
  it('formats a positive number with Colombian locale', () => {
    const result = formatPrice(3000000);
    expect(result).toContain('$');
    expect(result).toContain('3');
  });

  it('returns "$0" for zero', () => {
    const result = formatPrice(0);
    expect(result).toBe('$0');
  });

  it('returns empty string for null', () => {
    expect(formatPrice(null)).toBe('');
  });

  it('returns empty string for undefined', () => {
    expect(formatPrice(undefined)).toBe('');
  });

  it('returns empty string for empty string', () => {
    expect(formatPrice('')).toBe('');
  });
});


// ── Module selection logic ───────────────────────────────────────────────────

/**
 * Mirrors the module initialization logic from the watcher in InvestmentCalculatorModal.vue.
 * Builds the localModules array based on props.modules and saved localStorage selection.
 */
function buildLocalModules(modules, savedIds) {
  return modules.map(m => ({
    ...m,
    selected: savedIds ? savedIds.includes(m.id) : m.included !== false,
  }));
}

/**
 * Mirrors the dynamicTotal computed from InvestmentCalculatorModal.vue.
 */
function computeDynamicTotal(localModules) {
  return localModules.filter(m => m.selected).reduce((sum, m) => sum + (m.price || 0), 0);
}

/**
 * Mirrors the selectedCount computed from InvestmentCalculatorModal.vue.
 */
function computeSelectedCount(localModules) {
  return localModules.filter(m => m.selected).length;
}

describe('buildLocalModules', () => {
  it('uses included flag when no saved selection exists', () => {
    const result = buildLocalModules(MODULES_FIXTURE, null);
    expect(result[0].selected).toBe(true);   // web: included=true
    expect(result[1].selected).toBe(false);  // seo: included=false
    expect(result[2].selected).toBe(true);   // analytics: included=true
  });

  it('uses saved IDs when localStorage data exists', () => {
    const result = buildLocalModules(MODULES_FIXTURE, ['seo']);
    expect(result[0].selected).toBe(false);  // web: not in saved
    expect(result[1].selected).toBe(true);   // seo: in saved
    expect(result[2].selected).toBe(false);  // analytics: not in saved
  });

  it('handles empty saved array — all deselected', () => {
    const result = buildLocalModules(MODULES_FIXTURE, []);
    expect(result.every(m => m.selected === false)).toBe(true);
  });

  it('handles empty modules array', () => {
    const result = buildLocalModules([], null);
    expect(result).toEqual([]);
  });

  it('preserves original module properties', () => {
    const result = buildLocalModules(MODULES_FIXTURE, null);
    expect(result[0].id).toBe('web');
    expect(result[0].name).toBe('Sitio Web');
    expect(result[0].price).toBe(3000000);
  });
});


describe('computeDynamicTotal', () => {
  it('sums prices of selected modules only', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, null);
    // web (3M) + analytics (200K) are selected by default
    const total = computeDynamicTotal(modules);
    expect(total).toBe(3200000);
  });

  it('returns 0 when nothing is selected', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, []);
    expect(computeDynamicTotal(modules)).toBe(0);
  });

  it('sums all when all selected', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, ['web', 'seo', 'analytics']);
    expect(computeDynamicTotal(modules)).toBe(3700000);
  });

  it('handles modules with missing price', () => {
    const mods = [{ id: 'x', name: 'X', included: true }];
    const modules = buildLocalModules(mods, null);
    expect(computeDynamicTotal(modules)).toBe(0);
  });
});


describe('computeSelectedCount', () => {
  it('counts selected modules', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, null);
    expect(computeSelectedCount(modules)).toBe(2);
  });

  it('returns 0 when none selected', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, []);
    expect(computeSelectedCount(modules)).toBe(0);
  });

  it('returns total count when all selected', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, ['web', 'seo', 'analytics']);
    expect(computeSelectedCount(modules)).toBe(3);
  });
});


// ── localStorage persistence ─────────────────────────────────────────────────

/**
 * Mirrors the confirmSelection logic: saves selected IDs to localStorage.
 */
function confirmSelection(localModules, proposalUuid) {
  const selectedIds = localModules.filter(m => m.selected).map(m => m.id);
  const storageKey = `proposal-${proposalUuid}-modules`;
  localStorage.setItem(storageKey, JSON.stringify(selectedIds));
  return { selectedIds, total: computeDynamicTotal(localModules) };
}

describe('confirmSelection — localStorage persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('saves selected module IDs to localStorage', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, null);
    confirmSelection(modules, PROPOSAL_UUID);

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    expect(stored).toEqual(['web', 'analytics']);
  });

  it('returns selected IDs and total', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, ['seo', 'analytics']);
    const result = confirmSelection(modules, PROPOSAL_UUID);
    expect(result.selectedIds).toEqual(['seo', 'analytics']);
    expect(result.total).toBe(700000);
  });

  it('overwrites previous localStorage data', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(['old-module']));
    const modules = buildLocalModules(MODULES_FIXTURE, ['web']);
    confirmSelection(modules, PROPOSAL_UUID);

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    expect(stored).toEqual(['web']);
  });

  it('stores empty array when nothing selected', () => {
    const modules = buildLocalModules(MODULES_FIXTURE, []);
    confirmSelection(modules, PROPOSAL_UUID);

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    expect(stored).toEqual([]);
  });
});


// ── Round-trip: save → restore ───────────────────────────────────────────────

describe('localStorage round-trip', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('restores selections from previously saved data', () => {
    // Step 1: user selects seo + analytics, saves
    const modules1 = buildLocalModules(MODULES_FIXTURE, ['seo', 'analytics']);
    confirmSelection(modules1, PROPOSAL_UUID);

    // Step 2: modal reopens — reads from localStorage
    const raw = localStorage.getItem(STORAGE_KEY);
    const saved = JSON.parse(raw);
    const modules2 = buildLocalModules(MODULES_FIXTURE, saved);

    expect(modules2[0].selected).toBe(false);  // web
    expect(modules2[1].selected).toBe(true);   // seo
    expect(modules2[2].selected).toBe(true);   // analytics
    expect(computeDynamicTotal(modules2)).toBe(700000);
  });

  it('falls back to included defaults when localStorage is empty', () => {
    const raw = localStorage.getItem(STORAGE_KEY);
    const saved = raw ? JSON.parse(raw) : null;
    const modules = buildLocalModules(MODULES_FIXTURE, saved);

    expect(modules[0].selected).toBe(true);   // web: included=true
    expect(modules[1].selected).toBe(false);  // seo: included=false
    expect(computeDynamicTotal(modules)).toBe(3200000);
  });

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem(STORAGE_KEY, 'not-valid-json{');
    let saved = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) saved = JSON.parse(raw);
    } catch {
      saved = null;
    }

    const modules = buildLocalModules(MODULES_FIXTURE, saved);
    // Falls back to included defaults
    expect(modules[0].selected).toBe(true);
    expect(modules[1].selected).toBe(false);
  });
});


// ── Timeline logic (weeksReduction / weeksAddition / dynamicWeeks) ──────────

/**
 * Mirrors weeksReduction computed from InvestmentCalculatorModal.vue.
 * Deselecting investment modules reduces ~1 week each.
 * Views/features reduce 1 week per 3 deselected.
 */
function computeWeeksReduction(localModules) {
  const deselected = localModules.filter(m => !m.selected && !m._locked);
  let reduction = 0;
  let viewsRemoved = 0;
  let featuresRemoved = 0;

  for (const mod of deselected) {
    if (mod._source === 'investment') {
      reduction += 1;
    } else if (mod.groupId === 'views') {
      viewsRemoved += 1;
    } else if (mod.groupId === 'features') {
      featuresRemoved += 1;
    }
  }
  reduction += Math.floor(viewsRemoved / 3);
  reduction += Math.floor(featuresRemoved / 3);
  return reduction;
}

/**
 * Mirrors weeksAddition computed from InvestmentCalculatorModal.vue.
 * Selecting calculator modules (non-invite) adds ~1 week each.
 */
function computeWeeksAddition(localModules) {
  const selected = localModules.filter(m => m.selected && m._source === 'calculator_module' && !m.is_invite);
  let addition = 0;
  for (const mod of selected) {
    if (mod.groupId?.startsWith('integration_') || mod._source === 'calculator_module') {
      addition += 1;
    }
  }
  return addition;
}

/**
 * Mirrors dynamicWeeks computed from InvestmentCalculatorModal.vue.
 */
function computeDynamicWeeks(baseWeeks, localModules) {
  if (!baseWeeks) return 0;
  return Math.max(1, baseWeeks - computeWeeksReduction(localModules) + computeWeeksAddition(localModules));
}

const TIMELINE_MODULES = [
  { id: 'mod-a', name: 'CRM', _source: 'investment', selected: true, _locked: false },
  { id: 'mod-b', name: 'E-commerce', _source: 'investment', selected: true, _locked: false },
  { id: 'mod-c', name: 'Core', _source: 'investment', selected: true, _locked: true },
];

const CALCULATOR_MODULES = [
  { id: 'pwa', name: 'PWA', _source: 'calculator_module', groupId: 'pwa_module', selected: false, _locked: false, is_invite: false },
  { id: 'ai', name: 'AI', _source: 'calculator_module', groupId: 'ai_module', selected: false, _locked: false, is_invite: true },
  { id: 'reports', name: 'Reports', _source: 'calculator_module', groupId: 'reports_alerts_module', selected: true, _locked: false, is_invite: false },
];

describe('computeWeeksReduction', () => {
  it('returns 0 when all investment modules are selected', () => {
    expect(computeWeeksReduction(TIMELINE_MODULES)).toBe(0);
  });

  it('returns 1 when one investment module is deselected', () => {
    const mods = TIMELINE_MODULES.map(m => m.id === 'mod-a' ? { ...m, selected: false } : { ...m });
    expect(computeWeeksReduction(mods)).toBe(1);
  });

  it('returns 2 when two investment modules are deselected', () => {
    const mods = TIMELINE_MODULES.map(m => m._locked ? { ...m } : { ...m, selected: false });
    expect(computeWeeksReduction(mods)).toBe(2);
  });

  it('does not count locked modules as deselected', () => {
    const mods = TIMELINE_MODULES.map(m => ({ ...m, selected: false }));
    expect(computeWeeksReduction(mods)).toBe(2);
  });

  it('reduces 1 week per 3 deselected views', () => {
    const views = [
      { id: 'v1', groupId: 'views', selected: false, _locked: false },
      { id: 'v2', groupId: 'views', selected: false, _locked: false },
      { id: 'v3', groupId: 'views', selected: false, _locked: false },
    ];
    expect(computeWeeksReduction(views)).toBe(1);
  });

  it('reduces 0 for 2 deselected views (less than 3)', () => {
    const views = [
      { id: 'v1', groupId: 'views', selected: false, _locked: false },
      { id: 'v2', groupId: 'views', selected: false, _locked: false },
    ];
    expect(computeWeeksReduction(views)).toBe(0);
  });
});

describe('computeWeeksAddition', () => {
  it('returns 0 when no calculator modules are selected', () => {
    const mods = CALCULATOR_MODULES.map(m => ({ ...m, selected: false }));
    expect(computeWeeksAddition(mods)).toBe(0);
  });

  it('returns 1 when one non-invite calculator module is selected', () => {
    expect(computeWeeksAddition(CALCULATOR_MODULES)).toBe(1);
  });

  it('does not count invite modules (AI)', () => {
    const mods = CALCULATOR_MODULES.map(m => ({ ...m, selected: true }));
    expect(computeWeeksAddition(mods)).toBe(2);
  });

  it('returns 2 when two non-invite calculator modules are selected', () => {
    const mods = CALCULATOR_MODULES.map(m => m.id === 'pwa' ? { ...m, selected: true } : { ...m });
    expect(computeWeeksAddition(mods)).toBe(2);
  });
});

describe('computeDynamicWeeks', () => {
  it('returns 0 when baseWeeks is 0', () => {
    expect(computeDynamicWeeks(0, TIMELINE_MODULES)).toBe(0);
  });

  it('returns baseWeeks when no changes', () => {
    expect(computeDynamicWeeks(12, TIMELINE_MODULES)).toBe(12);
  });

  it('reduces weeks when investment modules deselected', () => {
    const mods = TIMELINE_MODULES.map(m => m.id === 'mod-a' ? { ...m, selected: false } : { ...m });
    expect(computeDynamicWeeks(12, mods)).toBe(11);
  });

  it('adds weeks when calculator modules selected', () => {
    const mods = [
      ...TIMELINE_MODULES,
      ...CALCULATOR_MODULES.map(m => m.id === 'pwa' ? { ...m, selected: true } : { ...m }),
    ];
    expect(computeDynamicWeeks(12, mods)).toBe(14);
  });

  it('combines reduction and addition', () => {
    const mods = [
      ...TIMELINE_MODULES.map(m => m.id === 'mod-a' ? { ...m, selected: false } : { ...m }),
      ...CALCULATOR_MODULES.map(m => m.id === 'pwa' ? { ...m, selected: true } : { ...m }),
    ];
    expect(computeDynamicWeeks(12, mods)).toBe(13);
  });

  it('never goes below 1', () => {
    const manyDeselected = Array.from({ length: 10 }, (_, i) => ({
      id: `m${i}`, _source: 'investment', selected: false, _locked: false,
    }));
    expect(computeDynamicWeeks(3, manyDeselected)).toBe(1);
  });
});

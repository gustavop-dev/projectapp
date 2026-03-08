/**
 * Tests for FunctionalRequirementsModal logic.
 *
 * Covers: group prop structure, items rendering logic,
 * default prop values, and edge cases for empty/missing data.
 */

// ── Fixtures ─────────────────────────────────────────────────────────────────

const GROUP_FIXTURE = {
  icon: '🖥️',
  title: 'Vistas',
  description: 'Pantallas principales del sitio web.',
  items: [
    { icon: '🏠', name: 'Home', description: 'Landing page con CTAs.' },
    { icon: '📧', name: 'Contacto', description: 'Formulario de contacto.' },
    { icon: '📜', name: 'Términos', description: 'Políticas y condiciones.' },
  ],
};

const GROUP_NO_DESCRIPTION = {
  icon: '🧩',
  title: 'Componentes',
  description: '',
  items: [
    { icon: '🔝', name: 'Header', description: 'Logo y navegación.' },
  ],
};

const GROUP_EMPTY_ITEMS = {
  icon: '⚙️',
  title: 'Features',
  description: 'Funcionalidades interactivas.',
  items: [],
};

const GROUP_MINIMAL = {
  icon: '',
  title: '',
  description: '',
  items: [],
};

const DEFAULT_GROUP = {
  icon: '🧩',
  title: '',
  description: '',
  items: [],
};


// ── Group prop validation ────────────────────────────────────────────────────

/**
 * Mirrors the default prop structure from FunctionalRequirementsModal.vue.
 * Validates that the group object has the expected shape.
 */
function normalizeGroup(group) {
  return {
    icon: group?.icon || '🧩',
    title: group?.title || '',
    description: group?.description || '',
    items: group?.items || [],
  };
}

describe('normalizeGroup', () => {
  it('returns group data unchanged when all fields present', () => {
    const result = normalizeGroup(GROUP_FIXTURE);
    expect(result.icon).toBe('🖥️');
    expect(result.title).toBe('Vistas');
    expect(result.description).toBe('Pantallas principales del sitio web.');
    expect(result.items).toHaveLength(3);
  });

  it('defaults icon to puzzle emoji when missing', () => {
    const result = normalizeGroup({ title: 'Test', description: '', items: [] });
    expect(result.icon).toBe('🧩');
  });

  it('defaults icon to puzzle emoji when empty string', () => {
    const result = normalizeGroup(GROUP_MINIMAL);
    expect(result.icon).toBe('🧩');
  });

  it('defaults all fields when group is null', () => {
    const result = normalizeGroup(null);
    expect(result).toEqual(DEFAULT_GROUP);
  });

  it('defaults all fields when group is undefined', () => {
    const result = normalizeGroup(undefined);
    expect(result).toEqual(DEFAULT_GROUP);
  });

  it('preserves items array reference', () => {
    const result = normalizeGroup(GROUP_FIXTURE);
    expect(result.items).toBe(GROUP_FIXTURE.items);
  });
});


// ── Items structure validation ───────────────────────────────────────────────

describe('group items structure', () => {
  it('each item has icon, name, and description', () => {
    for (const item of GROUP_FIXTURE.items) {
      expect(item).toHaveProperty('icon');
      expect(item).toHaveProperty('name');
      expect(item).toHaveProperty('description');
    }
  });

  it('items should NOT have a price field (prices only in calculator)', () => {
    for (const item of GROUP_FIXTURE.items) {
      expect(item).not.toHaveProperty('price');
    }
  });

  it('handles group with no description', () => {
    const result = normalizeGroup(GROUP_NO_DESCRIPTION);
    expect(result.description).toBe('');
    expect(result.items).toHaveLength(1);
  });

  it('handles group with empty items array', () => {
    const result = normalizeGroup(GROUP_EMPTY_ITEMS);
    expect(result.items).toHaveLength(0);
    expect(result.description).toBe('Funcionalidades interactivas.');
  });
});


// ── Rendering conditions ─────────────────────────────────────────────────────

/**
 * Mirrors template v-if conditions from FunctionalRequirementsModal.vue.
 */
function shouldShowDescription(group) {
  return Boolean(group?.description);
}

function shouldShowItemsGrid(group) {
  return Boolean(group?.items && group.items.length > 0);
}

describe('rendering conditions', () => {
  it('shows description when non-empty', () => {
    expect(shouldShowDescription(GROUP_FIXTURE)).toBe(true);
  });

  it('hides description when empty string', () => {
    expect(shouldShowDescription(GROUP_NO_DESCRIPTION)).toBe(false);
  });

  it('hides description when group is null', () => {
    expect(shouldShowDescription(null)).toBe(false);
  });

  it('shows items grid when items exist', () => {
    expect(shouldShowItemsGrid(GROUP_FIXTURE)).toBe(true);
  });

  it('hides items grid when items is empty array', () => {
    expect(shouldShowItemsGrid(GROUP_EMPTY_ITEMS)).toBe(false);
  });

  it('hides items grid when items is undefined', () => {
    expect(shouldShowItemsGrid({ title: 'Test' })).toBe(false);
  });

  it('hides items grid when group is null', () => {
    expect(shouldShowItemsGrid(null)).toBe(false);
  });
});


// ── Item icon fallback ───────────────────────────────────────────────────────

/**
 * Mirrors the template fallback: {{ item.icon || '✅' }}.
 */
function getItemIcon(item) {
  return item?.icon || '✅';
}

describe('item icon fallback', () => {
  it('returns the item icon when present', () => {
    expect(getItemIcon({ icon: '🏠', name: 'Home', description: '' })).toBe('🏠');
  });

  it('falls back to checkmark when icon is empty', () => {
    expect(getItemIcon({ icon: '', name: 'Test', description: '' })).toBe('✅');
  });

  it('falls back to checkmark when icon is missing', () => {
    expect(getItemIcon({ name: 'Test', description: '' })).toBe('✅');
  });

  it('falls back to checkmark when item is null', () => {
    expect(getItemIcon(null)).toBe('✅');
  });
});


// ── Multiple groups simulation ───────────────────────────────────────────────

describe('multiple groups from functional requirements', () => {
  const GROUPS = [GROUP_FIXTURE, GROUP_NO_DESCRIPTION, GROUP_EMPTY_ITEMS];

  it('each group can be independently normalized', () => {
    const normalized = GROUPS.map(normalizeGroup);
    expect(normalized).toHaveLength(3);
    expect(normalized[0].title).toBe('Vistas');
    expect(normalized[1].title).toBe('Componentes');
    expect(normalized[2].title).toBe('Features');
  });

  it('total items across all groups is correct', () => {
    const totalItems = GROUPS.reduce((sum, g) => sum + (g.items?.length || 0), 0);
    expect(totalItems).toBe(4);
  });

  it('only groups with items should show the items grid', () => {
    const withItems = GROUPS.filter(shouldShowItemsGrid);
    expect(withItems).toHaveLength(2);
  });
});

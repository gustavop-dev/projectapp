import {
  HANDLE_TRACK,
  TABLE_DENSITY,
  alignClass,
  hideClass,
  isVisibleAt,
  minWidthFor,
  resolveColumns,
  trackListFor,
} from '~/utils/tableLayout';

describe('tableLayout — size inference', () => {
  it('sizes a column from its format when no size is declared', () => {
    // A name column is present so the flex promotion lands there and leaves the
    // inferred sizes alone — the shape every real table in the module has.
    const [, money, date, badge] = resolveColumns([
      { key: 'name' },
      { key: 'total', format: 'money' },
      { key: 'day', format: 'date' },
      { key: 'state', format: 'badge' },
    ]);

    expect(money.size).toBe('money');
    expect(date.size).toBe('date');
    expect(badge.size).toBe('badge');
  });

  it('gives a centre-aligned column the narrowest track', () => {
    const [day] = resolveColumns([
      { key: 'billing_day', align: 'center' },
      { key: 'name' },
    ]);

    // "Día" shows one or two characters; it must not claim a full column.
    expect(day.size).toBe('tiny');
    expect(day.track).toBe('2.75rem');
  });

  it('honours an explicit size over the inferred one', () => {
    // Tipo/Estado render badges through slots, so `format` cannot reveal them.
    const [name, type] = resolveColumns([
      { key: 'name' },
      { key: 'cost_type_label', size: 'badge' },
    ]);

    expect(name.size).toBe('flex');
    expect(type.size).toBe('badge');
  });
});

describe('tableLayout — exactly one flexible column', () => {
  it('promotes the first text column when none declares flex', () => {
    const resolved = resolveColumns([
      { key: 'concept' },
      { key: 'note' },
      { key: 'total', format: 'money' },
    ]);

    expect(resolved.filter((col) => col.size === 'flex')).toHaveLength(1);
    expect(resolved[0].size).toBe('flex');
    expect(resolved[0].width).toBe('100%');
  });

  it('uses the declared flex column instead of the first text one', () => {
    const resolved = resolveColumns([
      { key: 'code' },
      { key: 'name', size: 'flex' },
    ]);

    expect(resolved.filter((col) => col.size === 'flex')).toHaveLength(1);
    expect(resolved[1].size).toBe('flex');
    expect(resolved[0].size).toBe('text');
  });

  it('still leaves one flexible column when every column is fixed-size', () => {
    // Otherwise a wide screen would strand all the slack outside the table.
    const resolved = resolveColumns([
      { key: 'total', format: 'money' },
      { key: 'state', format: 'badge' },
    ]);

    expect(resolved.filter((col) => col.size === 'flex')).toHaveLength(1);
  });

  it('returns an empty list for no columns without inventing a flex column', () => {
    expect(resolveColumns([])).toEqual([]);
  });
});

describe('tableLayout — money grouping', () => {
  const resolved = resolveColumns([
    { key: 'name' },
    { key: 'price', align: 'right', group: 'money' },
    { key: 'monthly_price', align: 'right', group: 'money' },
    { key: 'monthly_cop_cost', format: 'money', group: 'money' },
    { key: 'frequency_label' },
  ]);
  const [, first, middle, last, after] = resolved;

  it('brackets the group with a wider gap and tightens the members', () => {
    expect(first.padClass).toContain('pl-6');
    expect(first.padClass).toContain('pr-1.5');
    expect(middle.padClass).toContain('pl-2');
    expect(middle.padClass).toContain('pr-1.5');
    expect(last.padClass).toContain('pr-6');
  });

  it('applies the same grouping to the header so labels sit over their values', () => {
    expect(last.headerPadClass).toContain('pr-6');
    expect(first.headerPadClass).toContain('pl-6');
  });

  it('keeps the right-aligned group clear of the left-aligned column after it', () => {
    // The gap that stops "EQUIV. COP MENSUAL" colliding with "FRECUENCIA".
    expect(last.alignClass).toBe('text-right');
    expect(after.alignClass).toBe('text-left');
    expect(last.padClass).toContain('pr-6');
  });

  it('leaves a lone grouped column on the default padding', () => {
    const [only] = resolveColumns([
      { key: 'total', format: 'money', group: 'money' },
      { key: 'name' },
    ]);

    expect(only.padClass).toBe(TABLE_DENSITY.cell);
  });

  it('does not group across a different group name', () => {
    const cols = resolveColumns([
      { key: 'name' },
      { key: 'a', group: 'money' },
      { key: 'b', group: 'other' },
    ]);

    expect(cols[1].padClass).toBe(TABLE_DENSITY.cell);
    expect(cols[2].padClass).toBe(TABLE_DENSITY.cell);
  });
});

describe('tableLayout — alignment', () => {
  it('defaults money to the right and everything else to the left', () => {
    expect(alignClass({ format: 'money' })).toBe('text-right');
    expect(alignClass({ key: 'name' })).toBe('text-left');
    expect(alignClass({ align: 'center' })).toBe('text-center');
  });

  it('lets an explicit align override the money default', () => {
    expect(alignClass({ format: 'money', align: 'left' })).toBe('text-left');
  });
});

describe('tableLayout — responsive', () => {
  it('emits table-cell classes for a table and block classes for a grid', () => {
    expect(hideClass({ hideBelow: 'md' }, 'table')).toBe('hidden md:table-cell');
    expect(hideClass({ hideBelow: 'lg' }, 'grid')).toBe('hidden lg:block');
    expect(hideClass({ key: 'name' }, 'table')).toBe('');
  });

  it('reports visibility per breakpoint', () => {
    const always = { key: 'name' };
    const mid = { key: 'price', hideBelow: 'md' };
    const wide = { key: 'method', hideBelow: 'lg' };

    expect(isVisibleAt(always, 'base')).toBe(true);
    expect(isVisibleAt(mid, 'base')).toBe(false);
    expect(isVisibleAt(mid, 'md')).toBe(true);
    expect(isVisibleAt(wide, 'md')).toBe(false);
    expect(isVisibleAt(wide, 'lg')).toBe(true);
  });

  it('drops hidden columns from the narrow track list but keeps them when wide', () => {
    const resolved = resolveColumns([
      { key: 'name' },
      { key: 'method', hideBelow: 'lg' },
      { key: 'total', format: 'money' },
    ]);

    const base = trackListFor(resolved, { breakpoint: 'base' });
    const lg = trackListFor(resolved, { breakpoint: 'lg' });

    // name + total + actions at base; the method track only appears at lg.
    expect(base.split(' ').length).toBeLessThan(lg.split(' ').length);
    expect(lg).toContain('max-content');
  });
});

describe('tableLayout — track list and min width', () => {
  const resolved = resolveColumns([
    { key: 'name' },
    { key: 'total', format: 'money' },
  ]);

  it('prepends the drag handle track only when there is a handle', () => {
    expect(trackListFor(resolved, { hasHandle: true }).startsWith(HANDLE_TRACK)).toBe(true);
    expect(trackListFor(resolved, { hasHandle: false }).startsWith(HANDLE_TRACK)).toBe(false);
  });

  it('appends an actions track only when actions are shown', () => {
    // Two columns: name + total, so 2 tracks bare and 3 with the actions column.
    expect(trackListFor(resolved, { hasActions: false })).toBe(
      'minmax(7rem, 1fr) minmax(7rem, max-content)',
    );
    expect(trackListFor(resolved, { hasActions: true })).toBe(
      'minmax(7rem, 1fr) minmax(7rem, max-content) 5.25rem',
    );
  });

  it('derives a min width in rem that grows with the visible columns', () => {
    const narrow = minWidthFor(resolved, { breakpoint: 'base' });
    const wide = minWidthFor(
      resolveColumns([
        { key: 'name' },
        { key: 'total', format: 'money' },
        { key: 'other', format: 'money' },
      ]),
      { breakpoint: 'base' },
    );

    expect(narrow).toMatch(/rem$/);
    expect(parseFloat(wide)).toBeGreaterThan(parseFloat(narrow));
  });

  it('counts the drag handle in the min width', () => {
    const withHandle = minWidthFor(resolved, { hasHandle: true });
    const without = minWidthFor(resolved, { hasHandle: false });

    expect(parseFloat(withHandle)).toBeGreaterThan(parseFloat(without));
  });
});

import { mount } from '@vue/test-utils';
import AccountingTable from '~/components/accounting/AccountingTable.vue';
import { formatMoney } from '~/utils/formatMoney';

const columns = [
  { key: 'concept', label: 'Concepto' },
  { key: 'amount', label: 'Valor', format: 'money', align: 'right' },
  { key: 'date', label: 'Fecha', format: 'date' },
  {
    key: 'status',
    label: 'Estado',
    format: 'badge',
    badgeTones: { paid: 'success', overdue: 'danger', pending: 'neutral' },
  },
];

const rows = [
  { id: 1, concept: 'Página web', amount: 2500000, date: '2026-05-01', status: 'paid' },
  { id: 2, concept: 'Hosting anual', amount: 350000, date: '2026-05-10', status: 'overdue' },
];

function mountTable(props = {}) {
  return mount(AccountingTable, {
    props: { columns, rows, ...props },
  });
}

describe('AccountingTable', () => {
  it('renders configured column headers', () => {
    const wrapper = mountTable();

    const headers = wrapper.findAll('th').map((th) => th.text());
    expect(headers).toEqual(['Concepto', 'Valor', 'Fecha', 'Estado', 'Acciones']);
  });

  it('shares the width across every column instead of piling it into one', () => {
    // Two bugs guarded at once: splitting the width evenly (a two-character day
    // as wide as the concept) and handing one column width:100%, which moved
    // all the dead space into the gap next to it.
    const wrapper = mountTable({
      columns: [
        { key: 'concept', label: 'Concepto', size: 'name' },
        { key: 'amount', label: 'Valor', format: 'money' },
        { key: 'day', label: 'Día', align: 'center' },
      ],
    });
    const widths = wrapper.findAll('th').map((th) => th.element.style.width);

    expect(widths).not.toContain('100%');
    expect(widths.every((width) => width.endsWith('%'))).toBe(true);
    expect(widths.reduce((sum, width) => sum + parseFloat(width), 0)).toBeCloseTo(100, 1);
    // Proportional to content: the concept outgrows the amount, which outgrows
    // the two-character day — nobody is levelled up to the same share.
    expect(parseFloat(widths[0])).toBeGreaterThan(parseFloat(widths[1]));
    expect(parseFloat(widths[1])).toBeGreaterThan(parseFloat(widths[2]));
  });

  it('caps the name column content so a long value cannot widen the table', () => {
    const wrapper = mountTable({
      columns: [
        { key: 'concept', label: 'Concepto', size: 'name' },
        { key: 'amount', label: 'Valor', format: 'money' },
      ],
    });
    const [concept, amount] = wrapper.find('[data-testid="accounting-row-1"]').findAll('td');

    // A <td>'s own max-width is ignored under auto layout, so the cap has to
    // live on the wrapper around the content.
    expect(concept.find('span').classes()).toContain('max-w-[22rem]');
    expect(concept.text()).toBe('Página web');
    expect(amount.find('span').classes()).not.toContain('max-w-[22rem]');
  });

  it('fills its card edge to edge — the width ceiling lives on the page, not the table', () => {
    const table = mountTable().find('table');

    expect(table.classes()).toContain('w-full');
    expect(table.classes().some((c) => c.startsWith('max-w-'))).toBe(false);
    expect(table.classes()).not.toContain('mx-auto');
    // The scroll floor still wins on a narrow screen.
    expect(table.element.style.minWidth).toMatch(/rem$/);
  });

  it('keeps fixed-width columns on a single line so rows keep their height', () => {
    const wrapper = mountTable();
    const amountHeader = wrapper.findAll('th')[1];

    expect(amountHeader.classes()).toContain('whitespace-nowrap');
    expect(amountHeader.classes()).toContain('text-right');
  });

  it('aligns each header the same way as its cells', () => {
    const wrapper = mountTable();
    const headers = wrapper.findAll('th');
    const cells = wrapper.find('[data-testid="accounting-row-1"]').findAll('td');

    // Right-aligned amount over right-aligned values; the misalignment that put
    // a right-aligned header next to a left-aligned one is what this guards.
    expect(headers[1].classes()).toContain('text-right');
    expect(cells[1].classes()).toContain('text-right');
    expect(headers[0].classes()).toContain('text-left');
    expect(cells[0].classes()).toContain('text-left');
  });

  it('hides a column marked hideBelow on narrow screens, header and cell alike', () => {
    const wrapper = mountTable({
      columns: [
        { key: 'concept', label: 'Concepto' },
        { key: 'date', label: 'Fecha', format: 'date', hideBelow: 'lg' },
      ],
    });

    expect(wrapper.findAll('th')[1].classes()).toContain('hidden');
    expect(wrapper.findAll('th')[1].classes()).toContain('lg:table-cell');
    const cell = wrapper.find('[data-testid="accounting-row-1"]').findAll('td')[1];
    expect(cell.classes()).toContain('lg:table-cell');
  });

  it('renders one row per record with data-testid', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="accounting-row-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="accounting-row-2"]').exists()).toBe(true);
  });

  it('formats money cells with formatMoney in COP', () => {
    const wrapper = mountTable();

    expect(wrapper.text()).toContain(formatMoney(2500000, 'COP'));
    expect(wrapper.text()).toContain(formatMoney(350000, 'COP'));
  });

  it('formats date cells with the system date standard instead of raw ISO', () => {
    const wrapper = mountTable();

    expect(wrapper.text()).toContain('Vie, 1 may 2026');
    expect(wrapper.text()).not.toContain('2026-05-01');
  });

  it('renders an em-dash for a null date instead of an empty cell', () => {
    // A cuenta with plazo cero has no due_date; the Vence column has to say
    // "no deadline" rather than look like a value that failed to load.
    const wrapper = mountTable({
      rows: [{ id: 3, concept: 'Pago inmediato', amount: 100, date: null, status: 'paid' }],
    });

    const cell = wrapper.find('[data-testid="accounting-row-3"]').findAll('td')[2];
    expect(cell.text()).toBe('—');
  });

  it('formats percent cells rounded to one decimal, subtle and right-aligned', () => {
    const wrapper = mountTable({
      columns: [
        { key: 'concept', label: 'Concepto' },
        { key: 'weight_pct', label: '%', format: 'percent', sortable: true },
      ],
      rows: [{ id: 1, concept: 'Google Ads', weight_pct: 41.666 }],
    });

    const cell = wrapper.find('[data-testid="accounting-row-1"]').findAll('td')[1];
    expect(cell.text()).toBe('41,7%');
    expect(cell.classes()).toContain('text-right');
    expect(cell.classes()).toContain('text-text-subtle');
  });

  it('percent columns sort through the shared header button', async () => {
    const wrapper = mountTable({
      columns: [{ key: 'weight_pct', label: '%', format: 'percent', sortable: true }],
      rows: [{ id: 1, weight_pct: 100 }],
    });

    await wrapper.find('[data-testid="accounting-sort-weight_pct"]').trigger('click');
    expect(wrapper.emitted('sort')).toEqual([['weight_pct']]);
  });

  it('applies badge tone classes from badgeTones config', () => {
    const wrapper = mountTable();

    const row1 = wrapper.find('[data-testid="accounting-row-1"]');
    expect(row1.find('span.rounded-full').classes()).toContain('bg-success-soft');

    const row2 = wrapper.find('[data-testid="accounting-row-2"]');
    expect(row2.find('span.rounded-full').classes()).toContain('bg-danger-soft');
  });

  it('emits edit with the row when the edit button is clicked', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="accounting-edit-1"]').trigger('click');

    expect(wrapper.emitted('edit')).toHaveLength(1);
    expect(wrapper.emitted('edit')[0]).toEqual([rows[0]]);
  });

  it('emits delete with the row when the delete button is clicked', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="accounting-delete-2"]').trigger('click');

    expect(wrapper.emitted('delete')).toHaveLength(1);
    expect(wrapper.emitted('delete')[0]).toEqual([rows[1]]);
  });

  it('hides the actions column when showActions is false', () => {
    const wrapper = mountTable({ showActions: false });

    expect(wrapper.text()).not.toContain('Acciones');
    expect(wrapper.find('[data-testid="accounting-edit-1"]').exists()).toBe(false);
  });

  it('renders the empty state when rows is empty', () => {
    const wrapper = mountTable({ rows: [] });

    expect(wrapper.text()).toContain('Sin registros.');
  });

  it('supports cell-<key> slot overrides receiving row and value', () => {
    const wrapper = mount(AccountingTable, {
      props: { columns, rows },
      slots: {
        'cell-concept': `<template #cell-concept="{ row, value }">
          <em data-testid="custom-cell">{{ value }} ({{ row.id }})</em>
        </template>`,
      },
    });

    const custom = wrapper.findAll('[data-testid="custom-cell"]');
    expect(custom).toHaveLength(2);
    expect(custom[0].text()).toBe('Página web (1)');
  });

  it('highlights search occurrences in default text cells with <mark>', () => {
    const wrapper = mountTable({ highlightQuery: 'web' });
    const marks = wrapper.findAll('mark');
    expect(marks).toHaveLength(1);
    expect(marks[0].text()).toBe('web');
    // Money cells are not highlighted.
    expect(wrapper.text()).toContain(formatMoney(2500000, 'COP'));
  });

  it('sortable columns render a button with aria-sort and emit sort', async () => {
    const sortableColumns = [
      { key: 'concept', label: 'Concepto', sortable: true },
      { key: 'amount', label: 'Valor', format: 'money' },
    ];
    const wrapper = mountTable({
      columns: sortableColumns,
      sortKey: 'concept',
      sortDir: 'desc',
    });
    const th = wrapper.find('th[aria-sort]');
    expect(th.attributes('aria-sort')).toBe('descending');

    await wrapper.find('[data-testid="accounting-sort-concept"]').trigger('click');
    expect(wrapper.emitted('sort')).toEqual([['concept']]);
  });

  it('non-sorted sortable columns expose aria-sort none', () => {
    const wrapper = mountTable({
      columns: [{ key: 'concept', label: 'Concepto', sortable: true }],
      sortKey: '',
    });
    expect(wrapper.find('th[aria-sort]').attributes('aria-sort')).toBe('none');
  });

  it('non-sorted sortable columns show the neutral sortable hint icon', () => {
    const wrapper = mountTable({
      columns: [
        { key: 'concept', label: 'Concepto', sortable: true },
        { key: 'amount', label: 'Valor', format: 'money' },
      ],
      sortKey: '',
    });
    expect(wrapper.findAll('[data-testid="sortable-hint"]')).toHaveLength(1);
  });

  it('active sorted column swaps the hint for the direction chevron', () => {
    const wrapper = mountTable({
      columns: [{ key: 'concept', label: 'Concepto', sortable: true }],
      sortKey: 'concept',
      sortDir: 'asc',
    });
    expect(wrapper.find('[data-testid="sortable-hint"]').exists()).toBe(false);
  });

  it('renders skeleton rows and aria-busy on the first load', () => {
    const wrapper = mountTable({ rows: [], loading: true, skeletonRows: 4 });

    expect(wrapper.attributes('aria-busy')).toBe('true');
    expect(wrapper.findAll('[data-testid="accounting-skeleton-row"]')).toHaveLength(4);
    expect(wrapper.findAll('[data-testid^="accounting-row-"]')).toHaveLength(0);
  });

  it('keeps the rows on screen while refetching over them', () => {
    // Every accounting mutation refetches, so swapping the table for
    // placeholders made a delete or an edit read as a full reload.
    const wrapper = mountTable({ loading: true });

    expect(wrapper.findAll('[data-testid="accounting-skeleton-row"]')).toHaveLength(0);
    expect(wrapper.findAll('[data-testid^="accounting-row-"]')).toHaveLength(2);
    expect(wrapper.attributes('aria-busy')).toBe('true');
  });

  it('announces the row count via an aria-live region when loaded', () => {
    const wrapper = mountTable();
    const liveRegion = wrapper.find('[aria-live="polite"]');

    expect(wrapper.attributes('aria-busy')).toBeUndefined();
    expect(liveRegion.exists()).toBe(true);
    expect(liveRegion.text()).toContain('2 registros');
  });

  it('announces the loading state via the aria-live region', () => {
    const wrapper = mountTable({ loading: true });

    expect(wrapper.find('[aria-live="polite"]').text()).toContain('Cargando');
  });

  it('renders the #empty slot instead of the fallback text', () => {
    const wrapper = mount(AccountingTable, {
      props: { columns, rows: [] },
      slots: { empty: '<p>No hay nada por aquí</p>' },
    });

    expect(wrapper.text()).toContain('No hay nada por aquí');
    expect(wrapper.text()).not.toContain('Sin registros.');
  });

  it('flashes only the row matching highlightId', () => {
    const wrapper = mountTable({ highlightId: 2 });

    expect(wrapper.find('[data-testid="accounting-row-2"]').classes())
      .toContain('accounting-row-flash');
    expect(wrapper.find('[data-testid="accounting-row-1"]').classes())
      .not.toContain('accounting-row-flash');
  });

  describe('rowTone', () => {
    it('defaults every row to bg-surface when no tone is given', () => {
      const wrapper = mountTable();

      expect(wrapper.find('[data-testid="accounting-row-1"]').classes())
        .toContain('bg-surface');
    });

    it('replaces bg-surface with the tone class rather than stacking it', () => {
      // Two background utilities of equal specificity would be resolved by
      // stylesheet order, so the tone has to win by being the only one.
      const wrapper = mountTable({
        rowTone: (row) => (row.id === 1 ? 'success' : 'warning'),
      });

      const first = wrapper.find('[data-testid="accounting-row-1"]').classes();
      expect(first).toContain('bg-success-soft');
      expect(first).not.toContain('bg-surface');

      const second = wrapper.find('[data-testid="accounting-row-2"]').classes();
      expect(second).toContain('bg-warning-soft');
      expect(second).not.toContain('bg-surface');
    });

    it('falls back to bg-surface for rows the tone returns null for', () => {
      const wrapper = mountTable({
        rowTone: (row) => (row.id === 1 ? 'success' : null),
      });

      expect(wrapper.find('[data-testid="accounting-row-2"]').classes())
        .toContain('bg-surface');
    });

    it('keeps the flash alongside a toned row', () => {
      const wrapper = mountTable({ rowTone: () => 'success', highlightId: 1 });

      const classes = wrapper.find('[data-testid="accounting-row-1"]').classes();
      expect(classes).toContain('bg-success-soft');
      expect(classes).toContain('accounting-row-flash');
    });
  });
});

/**
 * The header checkbox is page-scoped on purpose — the page owns any "select
 * every filtered row" affordance. Pinned down here because the arithmetic now
 * lives in utils/rowSelection, shared with IncomeGroupedTable.
 */
describe('AccountingTable — selección de filas', () => {
  it('adds the whole page to the selection from the header checkbox', async () => {
    const wrapper = mountTable({ selectable: true, selected: [99] });

    await wrapper.find('[data-testid="accounting-select-page"]').setValue(true);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([99, 1, 2]);
  });

  it('removes only the page rows when the header checkbox is unticked', async () => {
    const wrapper = mountTable({ selectable: true, selected: [1, 2, 99] });

    await wrapper.find('[data-testid="accounting-select-page"]').setValue(false);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([99]);
  });

  it('shows the header checkbox indeterminate while only part of the page is selected', () => {
    const wrapper = mountTable({ selectable: true, selected: [1] });

    const pageBox = wrapper.find('[data-testid="accounting-select-page"]').element;
    expect(pageBox.indeterminate).toBe(true);
    expect(pageBox.checked).toBe(false);
  });

  it('ticks one row without disturbing the ids selected elsewhere', async () => {
    const wrapper = mountTable({ selectable: true, selected: [99] });

    await wrapper.find('[data-testid="accounting-select-2"]').setValue(true);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([99, 2]);
  });
});

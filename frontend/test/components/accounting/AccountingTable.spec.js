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

  it('renders skeleton rows and aria-busy while loading', () => {
    const wrapper = mountTable({ loading: true, skeletonRows: 4 });

    expect(wrapper.attributes('aria-busy')).toBe('true');
    expect(wrapper.findAll('[data-testid="accounting-skeleton-row"]')).toHaveLength(4);
    expect(wrapper.findAll('[data-testid^="accounting-row-"]')).toHaveLength(0);
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
});

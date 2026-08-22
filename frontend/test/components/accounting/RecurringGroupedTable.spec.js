import { mount } from '@vue/test-utils';

jest.mock('vuedraggable', () => ({
  __esModule: true,
  default: {
    name: 'DraggableStub',
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue', 'end'],
    template: `
      <div>
        <template v-for="(element, index) in modelValue || []" :key="element.id ?? index">
          <slot name="item" :element="element" :index="index" />
        </template>
      </div>
    `,
  },
}));

// eslint-disable-next-line import/first
import RecurringGroupedTable from '~/components/accounting/RecurringGroupedTable.vue';

const columns = [
  { key: 'name', label: 'Nombre' },
  { key: 'monthly_cop_cost', label: 'Equiv. COP mensual', format: 'money' },
];

const groups = [
  {
    id: 1,
    name: 'Suscripciones de IA',
    monthlyCopTotal: 880000,
    rows: [
      { id: 18, name: 'Claude Code 20x', monthly_cop_cost: 800000 },
      { id: 19, name: 'Chat-GPT', monthly_cop_cost: 80000 },
    ],
  },
  {
    id: 2,
    name: 'Infraestructura',
    monthlyCopTotal: 41059,
    rows: [{ id: 24, name: 'Hostinger', monthly_cop_cost: 32900 }],
  },
];

function mountTable(props = {}) {
  return mount(RecurringGroupedTable, {
    props: { columns, groups, ...props },
    global: { stubs: { HighlightText: true } },
  });
}

describe('RecurringGroupedTable', () => {
  it('renders one header per category with its monthly subtotal', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="recurring-group-1"]').text())
      .toContain('Suscripciones de IA');
    expect(wrapper.find('[data-testid="recurring-group-total-1"]').text())
      .toBe('$880.000 COP');
    expect(wrapper.find('[data-testid="recurring-group-total-2"]').text())
      .toBe('$41.059 COP');
  });

  it('shows the row count next to each category', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="recurring-group-1"]').text()).toContain('(2)');
  });

  it('labels the subtotal in its own block instead of chaining it to the name', () => {
    const wrapper = mountTable();

    const header = wrapper.find('[data-testid="recurring-group-1"]');
    // The amount carries its own label, so the block can be spread across the
    // row and still say what the figure is.
    expect(header.text()).toContain('Mensual');
    // The track spacing separates the blocks now, so the separator that used
    // to chain name and figure into one sentence is gone.
    expect(header.text()).not.toContain('·');
    // The count belongs to the category, so it stays with the name.
    expect(wrapper.find('[data-testid="recurring-group-toggle-1"]').text().replace(/\s+/g, ' '))
      .toContain('Suscripciones de IA(2)');
  });

  it('totals every group in the footer', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="recurring-monthly-grand-total"]').text())
      .toBe('$921.059 COP');
  });

  it('renders rows in the order the group provides', () => {
    const wrapper = mountTable();

    const names = wrapper.findAll('[data-testid^="accounting-row-"]')
      .map((row) => row.find('[role="cell"]').text());
    expect(names).toEqual(['Claude Code 20x', 'Chat-GPT', 'Hostinger']);
  });

  it('groups secondary business columns below the primary payment name', () => {
    const wrapper = mountTable({
      columns: [
        {
          ...columns[0],
          responsive: { primary: true, compact: 'keep', portrait: 'keep', landscape: 'keep' },
        },
        {
          ...columns[1],
          responsive: { compact: 'group', portrait: 'group', landscape: 'keep' },
        },
      ],
    });

    const details = wrapper.find('[data-testid="accounting-row-18"]')
      .get('[data-testid="responsive-group-compact"]');
    expect(details.text()).toContain('Equiv. COP mensual');
    expect(details.text()).toContain('$800.000 COP');
  });

  it('hides the drag handles when reordering is disabled', () => {
    const wrapper = mountTable({ dragEnabled: false });

    expect(wrapper.find('[data-testid="recurring-drag-handle-18"]').exists()).toBe(false);
  });

  it('shows a drag handle per row when reordering is enabled', () => {
    const wrapper = mountTable({ dragEnabled: true });

    expect(wrapper.find('[data-testid="recurring-drag-handle-18"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="recurring-drag-handle-24"]').exists()).toBe(true);
  });

  it('keeps the drag column header in the grid flow so labels align with cells', () => {
    const wrapper = mountTable({ dragEnabled: true });

    const headerRow = wrapper.find('[role="row"]');
    const headerCells = Array.from(headerRow.element.children);
    const bodyCells = Array.from(
      wrapper.find('[data-testid="accounting-row-18"]').element.children,
    );

    // Same in-flow grid items on both sides: orden + columns + acciones.
    expect(headerCells).toHaveLength(bodyCells.length);
    // sr-only is position:absolute — a direct child carrying it leaves the grid
    // flow and shifts every label one track left.
    expect(headerCells.filter((cell) => cell.classList.contains('sr-only'))).toEqual([]);
    expect(headerRow.text()).toContain('Orden');
  });

  it('declares the track list once on the container, never per row', () => {
    const wrapper = mountTable({ dragEnabled: true });

    const container = wrapper.find('.accounting-grid-scroll');
    const headerRow = wrapper.find('[role="row"]');
    const bodyRow = wrapper.find('[data-testid="accounting-row-18"]');

    // The whole point: a row that carries its own track list resolves it
    // against its own cells, so the one row with a wider value drifts out of
    // column. The container declares them and the rows inherit.
    const containerStyle = container.attributes('style');
    expect(containerStyle).toContain('--cols-compact');
    expect(containerStyle).toContain('--cols-portrait');
    expect(containerStyle).toContain('--cols-landscape');
    expect(containerStyle).toContain('--cols-desktop');
    expect(headerRow.attributes('style')).toBeUndefined();
    expect(bodyRow.attributes('style')).toBeUndefined();
    expect(headerRow.classes()).toContain('accounting-grid-row');
    expect(bodyRow.classes()).toContain('accounting-grid-row');
  });

  it('keeps the subgrid chain unbroken between the container and its rows', () => {
    const wrapper = mountTable({ dragEnabled: true });

    // Every wrapper between the container and a row has to pass the columns
    // down; one plain div in the middle and the rows stop seeing them.
    expect(wrapper.find('[role="rowgroup"]').classes()).toContain('accounting-grid-subgrid');
    expect(wrapper.findComponent({ name: 'DraggableStub' }).classes())
      .toContain('accounting-grid-subgrid');
    // Bands are not column-structured: they span instead of sizing a column.
    expect(wrapper.find('[data-testid="recurring-group-1"]').classes())
      .toContain('accounting-grid-band');
    expect(wrapper.find('[data-testid="recurring-monthly-grand-total"]')
      .element.closest('[role="row"]').className).toContain('accounting-grid-band');
  });

  it('gives every column a content floor and a proportional share of the slack', () => {
    const wrapper = mountTable({
      dragEnabled: true,
      columns: [
        ...columns,
        { key: 'billing_day', label: 'Día', align: 'center' },
        { key: 'is_active', label: 'Estado', size: 'badge' },
      ],
    });
    const wide = wrapper
      .find('.accounting-grid-scroll')
      .attributes('style')
      .match(/--cols-desktop:([^;]*)/)[1];

    // No single track hoards the slack: each one floors at its content and
    // grows by its own weight, so a two-character day stays narrow while an
    // amount does not, and neither is separated by an outsized gap.
    expect(wide).toContain('minmax(max-content, 2.75fr)'); // Día
    expect(wide).toContain('minmax(max-content, 6fr)'); // Estado badge
    expect(wide).toContain('minmax(max-content, 7fr)'); // monto
    // Four data columns plus the actions slot; the drag handle stays fixed.
    expect(wide.match(/minmax\(max-content, [\d.]+fr\)/g)).toHaveLength(5);
    expect(wide).toContain('1.75rem');
  });

  it('caps the name column content so a long value cannot widen the grid', () => {
    const wrapper = mountTable({
      dragEnabled: true,
      columns: [{ key: 'name', label: 'Nombre', size: 'name' }, columns[1]],
    });
    const nameCell = wrapper
      .find('[data-testid="accounting-row-18"]')
      .findAll('[role="cell"]')
      .find((cell) => cell.text().includes('Claude Code 20x'));

    expect(nameCell.get('div').classes()).toContain('max-w-[22rem]');
  });

  it('emits the full board with category and order after a drag', async () => {
    const wrapper = mountTable({ dragEnabled: true });

    await wrapper.findAllComponents({ name: 'DraggableStub' })[0].vm.$emit('end');

    expect(wrapper.emitted('reorder')[0][0]).toEqual([
      { id: 18, category: 1, order: 0 },
      { id: 19, category: 1, order: 1 },
      { id: 24, category: 2, order: 0 },
    ]);
  });

  it('maps the uncategorized bucket back to a null category', async () => {
    const wrapper = mountTable({
      dragEnabled: true,
      groups: [{
        id: 'uncategorized',
        name: 'Sin categoría',
        monthlyCopTotal: 1000,
        rows: [{ id: 30, name: 'Suelto', monthly_cop_cost: 1000 }],
      }],
    });

    await wrapper.findAllComponents({ name: 'DraggableStub' })[0].vm.$emit('end');

    expect(wrapper.emitted('reorder')[0][0]).toEqual([
      { id: 30, category: null, order: 0 },
    ]);
  });

  it('emits toggle-group when a category header is clicked', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="recurring-group-toggle-1"]').trigger('click');

    expect(wrapper.emitted('toggle-group')[0]).toEqual([1]);
  });

  it('marks a collapsed group as not expanded', () => {
    const wrapper = mountTable({ collapsedIds: [1] });

    expect(
      wrapper.find('[data-testid="recurring-group-toggle-1"]').attributes('aria-expanded'),
    ).toBe('false');
    expect(
      wrapper.find('[data-testid="recurring-group-toggle-2"]').attributes('aria-expanded'),
    ).toBe('true');
  });

  it('shows each group\'s weight next to its subtotal when provided', () => {
    const wrapper = mountTable({
      groups: groups.map((group, index) => ({ ...group, groupWeightPct: index === 0 ? 95.5 : 4.5 })),
    });

    expect(wrapper.find('[data-testid="recurring-group-weight-1"]').text()).toBe('95,5%');
    expect(wrapper.find('[data-testid="recurring-group-weight-2"]').text()).toBe('4,5%');
    // The label says what the figure is — this group's share OF the active
    // payments — instead of trailing the row unlabelled or reading as how
    // much of the group is active.
    expect(wrapper.find('[data-testid="recurring-group-1"]').text())
      .toContain('Participación en pagos activos');
  });

  it('omits the group weight when the page does not compute one', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="recurring-group-weight-1"]').exists()).toBe(false);
  });

  it('the weight-sort header button emits toggle-weight-sort', async () => {
    const wrapper = mountTable({ sortColumnKey: 'monthly_cop_cost' });

    await wrapper.find('[data-testid="recurring-grouped-sort-weight"]').trigger('click');

    expect(wrapper.emitted('toggle-weight-sort')).toHaveLength(1);
  });

  it('reflects the weight-sort state through aria-sort on the column header', async () => {
    const wrapper = mountTable({ sortColumnKey: 'monthly_cop_cost', weightSort: 'desc' });

    const header = wrapper.find('[role="columnheader"][aria-sort]');
    expect(header.attributes('aria-sort')).toBe('descending');

    await wrapper.setProps({ weightSort: '' });
    expect(wrapper.find('[role="columnheader"][aria-sort]').attributes('aria-sort')).toBe('none');
  });

  it('renders plain headers when no sort column is configured', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="recurring-grouped-sort-weight"]').exists()).toBe(false);
  });

  it('emits edit and delete for a row', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="accounting-edit-18"]').trigger('click');
    await wrapper.find('[data-testid="accounting-delete-18"]').trigger('click');

    expect(wrapper.emitted('edit')[0][0].id).toBe(18);
    expect(wrapper.emitted('delete')[0][0].id).toBe(18);
  });

  it('lets a cell slot override the default rendering', () => {
    const wrapper = mount(RecurringGroupedTable, {
      props: { columns, groups },
      slots: { 'cell-name': '<span data-testid="slot-override">reemplazo</span>' },
      global: { stubs: { HighlightText: true } },
    });

    expect(wrapper.find('[data-testid="slot-override"]').text()).toBe('reemplazo');
  });

  it('renders skeleton rows instead of groups on the first load', () => {
    const wrapper = mountTable({ groups: [], loading: true });

    expect(wrapper.find('[data-testid="accounting-skeleton-row"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="recurring-group-1"]').exists()).toBe(false);
  });

  it('keeps the groups on screen while refetching over them', () => {
    const wrapper = mountTable({ loading: true });

    expect(wrapper.find('[data-testid="accounting-skeleton-row"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="recurring-group-1"]').exists()).toBe(true);
  });
});

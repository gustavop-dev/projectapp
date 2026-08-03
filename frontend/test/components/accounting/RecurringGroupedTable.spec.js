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

  it('drives header and rows from one track list so they cannot drift apart', () => {
    const wrapper = mountTable({ dragEnabled: true });

    const headerRow = wrapper.find('[role="row"]');
    const bodyRow = wrapper.find('[data-testid="accounting-row-18"]');

    // Both carry the class the media queries target, and the same per-breakpoint
    // track lists — one column config, one geometry.
    expect(headerRow.classes()).toContain('accounting-grid-row');
    expect(bodyRow.classes()).toContain('accounting-grid-row');
    expect(headerRow.attributes('style')).toBe(bodyRow.attributes('style'));
  });

  it('sizes columns by content instead of splitting the width evenly', () => {
    const wrapper = mountTable({
      dragEnabled: true,
      columns: [
        ...columns,
        { key: 'billing_day', label: 'Día', align: 'center' },
        { key: 'is_active', label: 'Estado', size: 'badge' },
      ],
    });
    const wide = wrapper
      .find('[role="row"]')
      .attributes('style')
      .match(/--cols-lg:([^;]*)/)[1];

    // Exactly one flexible track absorbs the slack; everything else is fixed,
    // so a badge or a two-character day no longer claims a full column.
    expect(wide.match(/1fr/g)).toHaveLength(1);
    expect(wide).toContain('2.75rem'); // Día
    expect(wide).toContain('6rem'); // Estado badge
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

  it('renders skeleton rows while loading instead of groups', () => {
    const wrapper = mountTable({ loading: true });

    expect(wrapper.find('[data-testid="accounting-skeleton-row"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="recurring-group-1"]').exists()).toBe(false);
  });
});

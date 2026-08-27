import { mount } from '@vue/test-utils';

import IncomeGroupedTable from '~/components/accounting/IncomeGroupedTable.vue';

const columns = [
  { key: 'concept', label: 'Concepto', size: 'name' },
  { key: 'total_amount', label: 'Total', format: 'money' },
];

// Shape of withClientWeights(groupByClient(rows)): ordered by billed,
// unassigned bucket last.
function makeGroups() {
  return [
    {
      id: 22,
      name: 'Deivis Rios',
      count: 2,
      billed: 7646746,
      collected: 1000000,
      pending: 6646746,
      lost: 0,
      weightPct: 88.4,
      rows: [
        { id: 217, concept: 'Vastago - Abono inicial', total_amount: '6000000.00' },
        { id: 218, concept: 'Vastago - Cuota 1/12', total_amount: '1646746.00' },
      ],
    },
    {
      id: 'none',
      name: 'Sin cliente',
      count: 1,
      billed: 1000000,
      collected: 0,
      pending: 1000000,
      lost: 0,
      weightPct: 11.6,
      rows: [{ id: 300, concept: 'Reembolso banco', total_amount: '1000000.00' }],
    },
  ];
}

function mountTable(props = {}, options = {}) {
  return mount(IncomeGroupedTable, {
    props: { columns, groups: makeGroups(), ...props },
    global: { stubs: { HighlightText: true } },
    ...options,
  });
}

describe('IncomeGroupedTable', () => {
  it('renders one header per client with its billed subtotal', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="income-group-22"]').text())
      .toContain('Deivis Rios');
    expect(wrapper.find('[data-testid="income-group-billed-22"]').text())
      .toBe('$7.646.746 COP');
    expect(wrapper.find('[data-testid="income-group-22"]').text()).toContain('(2)');
  });

  it('shows the pending subtotal and the weight share in the header', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="income-group-pending-22"]').text())
      .toBe('$6.646.746 COP');
    expect(wrapper.find('[data-testid="income-group-weight-22"]').text())
      .toBe('88,4%');
    // The label has to say what the figure IS — this group's share of the
    // billed total — and not "% de lo facturado", which also reads as how
    // much of this group is billed, a different question.
    expect(wrapper.find('[data-testid="income-group-22"]').text())
      .toContain('Participación en lo facturado');
  });

  it('labels every figure in its own block instead of chaining them with middots', () => {
    const wrapper = mountTable();

    const header = wrapper.find('[data-testid="income-group-22"]');
    // Each amount carries its own label above its value, so the reader never
    // loses which figure is which.
    expect(header.text()).toContain('Facturado');
    expect(header.text()).toContain('Pendiente');
    // With every block labelled, the gap alone tells them apart: the middots
    // that used to chain name and figures into one sentence are gone.
    expect(header.text()).not.toContain('·');
  });

  it('keeps the three figures as siblings right after the client name', () => {
    const wrapper = mountTable();

    // The figures are facts about the client they follow, so they stay
    // contiguous to the name at the start of the band — one flat row of
    // blocks, in reading order. Nesting or reordering them is what turned
    // them back into columns of something else.
    const blocks = wrapper.find('[data-testid="income-group-22"]').element.children;
    expect(blocks.length).toBe(4);
    expect(blocks[0].textContent).toContain('Deivis Rios');
    expect(blocks[1].textContent).toContain('Facturado');
    expect(blocks[2].textContent).toContain('Pendiente');
    expect(blocks[3].textContent).toContain('Participación en lo facturado');
  });

  it('keeps the record count with the client name, not with the amounts', () => {
    const wrapper = mountTable();

    // The count belongs to the client, so it stays inside the name's toggle
    // rather than drifting into the figures.
    expect(wrapper.find('[data-testid="income-group-toggle-22"]').text().replace(/\s+/g, ' '))
      .toContain('Deivis Rios(2)');
  });

  it('spells out a zero subtotal instead of dropping the term', () => {
    const groups = makeGroups();
    groups[0].billed = 0;
    groups[0].pending = 0;
    const wrapper = mountTable({ groups });

    expect(wrapper.find('[data-testid="income-group-billed-22"]').text())
      .toBe('$0 COP');
    expect(wrapper.find('[data-testid="income-group-pending-22"]').text())
      .toBe('$0 COP');
  });

  it('renders the unassigned bucket last, flagged "por completar"', () => {
    const wrapper = mountTable();

    const headers = wrapper.findAll(
      '[data-testid="income-group-22"], [data-testid="income-group-none"]',
    );
    expect(headers.map((header) => header.attributes('data-testid')))
      .toEqual(['income-group-22', 'income-group-none']);
    expect(wrapper.find('[data-testid="income-group-none"]').text())
      .toContain('Sin cliente');
    expect(wrapper.find('[data-testid="income-group-none"]').text())
      .toContain('por completar');
  });

  it('sums billed, collected and pending across every group in the footer', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="income-grouped-billed-total"]').text())
      .toBe('$8.646.746 COP');
    expect(wrapper.find('[data-testid="income-grouped-collected-total"]').text())
      .toBe('$1.000.000 COP');
    expect(wrapper.find('[data-testid="income-grouped-pending-total"]').text())
      .toBe('$7.646.746 COP');
  });

  it('renders the rows in the order each group provides', () => {
    const wrapper = mountTable();

    const concepts = wrapper.findAll('[data-testid^="accounting-row-"]')
      .map((row) => row.find('[role="cell"]').text());
    expect(concepts).toEqual([
      'Vastago - Abono inicial', 'Vastago - Cuota 1/12', 'Reembolso banco',
    ]);
  });

  it('orders the leading grouped-table controls', () => {
    const wrapper = mountTable({
      selectable: true,
      showDefaultActions: false,
      rowActionsLayout: 'menu-start',
    }, {
      slots: {
        'row-actions': '<button data-testid="income-kebab">Acciones</button>',
      },
    });

    const headers = wrapper.get('.accounting-grid-row[role="row"]')
      .findAll('[role="columnheader"]');
    expect(headers[0].find('input[type="checkbox"]').exists()).toBe(true);
    expect(headers[1].attributes('data-testid')).toBe('accounting-actions-header');
    expect(headers[2].text()).toBe('Concepto');

    const cells = wrapper.get('[data-testid="accounting-row-217"]')
      .findAll('[role="cell"]');
    expect(cells[1].attributes('data-testid')).toBe('accounting-actions-cell-217');
    expect(cells[2].text()).toContain('Vastago - Abono inicial');
  });

  it('renders one blank grouped-table menu slot', () => {
    const wrapper = mountTable({
      selectable: true,
      showDefaultActions: false,
      rowActionsLayout: 'menu-start',
    }, {
      slots: {
        'row-actions': '<button data-testid="income-kebab">Acciones</button>',
      },
    });
    const header = wrapper.get('[data-testid="accounting-actions-header"]');
    const cell = wrapper.get('[data-testid="accounting-actions-cell-217"]');

    expect(header.attributes('aria-label')).toBe('Acciones');
    expect(header.text()).toBe('');
    expect(cell.findAll('[data-testid="income-kebab"]')).toHaveLength(1);
  });

  it('groups secondary business columns below the primary concept', () => {
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

    const details = wrapper.find('[data-testid="accounting-row-217"]')
      .get('[data-testid="responsive-group-compact"]');
    expect(details.text()).toContain('Total');
    expect(details.text()).toContain('$6.000.000 COP');
  });

  it('emits edit and delete with the clicked row', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="accounting-edit-217"]').trigger('click');
    await wrapper.find('[data-testid="accounting-delete-300"]').trigger('click');

    expect(wrapper.emitted('edit')[0][0].id).toBe(217);
    expect(wrapper.emitted('delete')[0][0].id).toBe(300);
  });

  it('emits toggle-group with the group id from the header button', async () => {
    const wrapper = mountTable();

    await wrapper.find('[data-testid="income-group-toggle-none"]').trigger('click');

    expect(wrapper.emitted('toggle-group')[0]).toEqual(['none']);
  });

  it('collapses the listed groups and reflects it on aria-expanded', () => {
    const wrapper = mountTable({ collapsedIds: [22] });

    // v-show: assert the inline style, not isVisible() — jsdom caches
    // getComputedStyle across v-show toggles.
    expect(wrapper.find('#income-group-body-22').element.style.display)
      .toBe('none');
    expect(wrapper.find('#income-group-body-none').element.style.display)
      .not.toBe('none');
    expect(
      wrapper.find('[data-testid="income-group-toggle-22"]').attributes('aria-expanded'),
    ).toBe('false');
  });

  it('exposes a row-actions slot rendered next to edit/delete', () => {
    const wrapper = mountTable({}, {
      slots: {
        'row-actions': `
          <template #row-actions="{ row }">
            <button :data-testid="'extra-action-' + row.id">extra</button>
          </template>
        `,
      },
    });

    expect(wrapper.find('[data-testid="extra-action-217"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="extra-action-300"]').exists()).toBe(true);
  });

  it('lets a cell slot override the default rendering', () => {
    const wrapper = mountTable({}, {
      slots: {
        'cell-concept': `
          <template #cell-concept="{ row }">
            <em :data-testid="'fancy-' + row.id">{{ row.concept }}!</em>
          </template>
        `,
      },
    });

    expect(wrapper.find('[data-testid="fancy-217"]').text())
      .toBe('Vastago - Abono inicial!');
  });

  it('shows skeleton rows on the first load', () => {
    const wrapper = mountTable({ groups: [], loading: true, skeletonRows: 3 });

    expect(wrapper.findAll('[data-testid="accounting-skeleton-row"]')).toHaveLength(3);
    expect(wrapper.find('[data-testid="income-group-22"]').exists()).toBe(false);
  });

  it('keeps the groups and their counters on screen while refetching', () => {
    // Blanking the grid on every mutation took the group counters and the
    // totals row with it, so a delete looked like a reload instead of a
    // recount.
    const wrapper = mountTable({ loading: true });

    expect(wrapper.findAll('[data-testid="accounting-skeleton-row"]')).toHaveLength(0);
    expect(wrapper.find('[data-testid="income-group-22"]').text()).toContain('(2)');
  });

  it('flashes the highlighted row', () => {
    const wrapper = mountTable({ highlightId: 218 });

    expect(wrapper.find('[data-testid="accounting-row-218"]').classes())
      .toContain('accounting-row-flash');
    expect(wrapper.find('[data-testid="accounting-row-217"]').classes())
      .not.toContain('accounting-row-flash');
  });
});

/**
 * The bulk client assignment is what this view was missing: "Sin cliente" is
 * visible here and nowhere else, so the rows that need a client have to be
 * selectable without leaving the grouping behind.
 */
describe('IncomeGroupedTable — selección múltiple', () => {
  function mountSelectable(props = {}) {
    return mountTable({ selectable: true, selected: [], ...props });
  }

  it('renders no checkbox at all unless the page asks for selection', () => {
    const wrapper = mountTable();

    expect(wrapper.find('[data-testid="accounting-select-217"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="income-group-select-22"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="accounting-select-all"]').exists()).toBe(false);
  });

  it('adds the row to the selection when its checkbox is ticked', async () => {
    const wrapper = mountSelectable({ selected: [300] });

    await wrapper.find('[data-testid="accounting-select-217"]').setValue(true);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([300, 217]);
  });

  it('drops the row from the selection when its checkbox is unticked', async () => {
    const wrapper = mountSelectable({ selected: [217, 300] });

    await wrapper.find('[data-testid="accounting-select-217"]').setValue(false);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([300]);
  });

  it('selects every row of a group — and only that group — from its header', async () => {
    const wrapper = mountSelectable();

    await wrapper.find('[data-testid="income-group-select-22"]').setValue(true);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([217, 218]);
  });

  it('clears just that group when its header checkbox is unticked', async () => {
    const wrapper = mountSelectable({ selected: [217, 218, 300] });

    await wrapper.find('[data-testid="income-group-select-22"]').setValue(false);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([300]);
  });

  it('shows the group checkbox indeterminate while only part of it is selected', () => {
    const wrapper = mountSelectable({ selected: [217] });

    const groupBox = wrapper.find('[data-testid="income-group-select-22"]').element;
    expect(groupBox.indeterminate).toBe(true);
    expect(groupBox.checked).toBe(false);
  });

  it('ticks the group checkbox once every row of the group is selected', () => {
    const wrapper = mountSelectable({ selected: [217, 218] });

    const groupBox = wrapper.find('[data-testid="income-group-select-22"]').element;
    expect(groupBox.checked).toBe(true);
    expect(groupBox.indeterminate).toBe(false);
  });

  // No pagination here: the groups ARE the filtered set, so "todos" cannot
  // reach beyond what the active filters left on screen.
  it('selects every row of every group from the header checkbox', async () => {
    const wrapper = mountSelectable();

    await wrapper.find('[data-testid="accounting-select-all"]').setValue(true);

    expect(wrapper.emitted('update:selected')[0][0]).toEqual([217, 218, 300]);
  });

  it('shows the header checkbox indeterminate while a group is only partly selected', () => {
    const wrapper = mountSelectable({ selected: [217, 218] });

    const allBox = wrapper.find('[data-testid="accounting-select-all"]').element;
    expect(allBox.indeterminate).toBe(true);
    expect(allBox.checked).toBe(false);
  });

  it('reports how much of a collapsed group is selected, since it still counts', () => {
    const wrapper = mountSelectable({ selected: [217], collapsedIds: [22] });

    expect(wrapper.find('[data-testid="income-group-selected-22"]').text())
      .toBe('1 seleccionado');
    // The open group says nothing: its ticked rows are on screen.
    expect(wrapper.find('[data-testid="income-group-selected-none"]').exists())
      .toBe(false);
  });

  it('keeps the collapsed badge quiet when nothing in that group is selected', () => {
    const wrapper = mountSelectable({ selected: [300], collapsedIds: [22] });

    expect(wrapper.find('[data-testid="income-group-selected-22"]').exists())
      .toBe(false);
  });
});

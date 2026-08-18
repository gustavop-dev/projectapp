import { mount } from '@vue/test-utils';
import AccountingFilterPanel from '../../../components/accounting/AccountingFilterPanel.vue';

const FIELDS = [
  { kind: 'range', label: 'Total', minKey: 'amountMin', maxKey: 'amountMax', type: 'number' },
  {
    kind: 'segmented',
    key: 'kind',
    label: 'Tipo',
    options: [
      { value: '', label: 'Todos' },
      { value: 'liquid', label: 'Líquido' },
    ],
  },
  {
    kind: 'multi',
    key: 'categories',
    label: 'Categoría',
    options: [
      { value: 'business', label: 'Negocio' },
      { value: 'personal', label: 'Personal' },
    ],
  },
];

function mountPanel(props = {}) {
  return mount(AccountingFilterPanel, {
    props: {
      fields: FIELDS,
      modelValue: { amountMin: '', amountMax: '', kind: '', categories: [] },
      isOpen: true,
      resultsCount: 7,
      searchValue: '',
      ...props,
    },
    global: {
      stubs: {
        ProposalFilterDropdown: true,
        ProposalFilterRangeDropdown: true,
        BaseSegmentedMulti: true,
      },
    },
  });
}

describe('AccountingFilterPanel', () => {
  it('shows the results count', () => {
    const wrapper = mountPanel();
    expect(wrapper.find('[data-testid="accounting-results-count"]').text())
      .toBe('7 resultados');
    expect(mountPanel({ resultsCount: 1 })
      .find('[data-testid="accounting-results-count"]').text())
      .toBe('1 resultado');
  });

  it('renders one removable chip per applied filter', () => {
    const wrapper = mountPanel({
      modelValue: {
        amountMin: '100', amountMax: '500', kind: 'liquid',
        categories: ['business', 'personal'],
      },
      searchValue: 'kore',
    });
    const chips = wrapper.findAll('[data-testid="accounting-filter-chip"]');
    const labels = chips.map((chip) => chip.text());
    expect(labels).toContain('"kore"');
    expect(labels).toContain('Total: 100 – 500');
    expect(labels).toContain('Tipo: Líquido');
    // One chip per DIMENSION listing its values, so a dimension with two
    // values chosen still reads as one cut and not as two unrelated filters.
    expect(labels).toContain('Categoría: Negocio, Personal');
  });

  it('lists every chosen value of a dimension in a single chip', () => {
    const wrapper = mountPanel({
      modelValue: {
        amountMin: '', amountMax: '', kind: ['liquid'], categories: ['business', 'personal'],
      },
    });
    const chip = wrapper.findAll('[data-testid="accounting-filter-chip"]')
      .find((c) => c.text().startsWith('Categoría'));
    expect(chip.text()).toBe('Categoría: Negocio, Personal');
    expect(chip.findAll('[data-testid="accounting-filter-chip-value"]')).toHaveLength(2);
  });

  it('removing one value of a dimension leaves the other applied', async () => {
    const wrapper = mountPanel({
      modelValue: {
        amountMin: '', amountMax: '', kind: [], categories: ['business', 'personal'],
      },
    });
    await wrapper
      .find('[data-testid="accounting-filter-chip-remove-categories-business"]')
      .trigger('click');
    expect(wrapper.emitted('update:modelValue')[0][0].categories).toEqual(['personal']);
  });

  it('reads a tab saved before the dimension went multi-valued', () => {
    // Stored scalar, not an array: it must still raise its chip instead of
    // looking like no filter at all.
    const wrapper = mountPanel({
      modelValue: { amountMin: '', amountMax: '', kind: 'liquid', categories: [] },
    });
    const labels = wrapper.findAll('[data-testid="accounting-filter-chip"]')
      .map((chip) => chip.text());
    expect(labels).toContain('Tipo: Líquido');
  });

  it('removing a chip clears only its filter keys', async () => {
    const wrapper = mountPanel({
      modelValue: {
        amountMin: '100', amountMax: '', kind: 'liquid', categories: ['business'],
      },
    });
    const rangeChip = wrapper
      .findAll('[data-testid="accounting-filter-chip"]')
      .find((chip) => chip.text().includes('Total'));
    await rangeChip.find('button').trigger('click');

    const emitted = wrapper.emitted('update:modelValue').at(-1)[0];
    expect(emitted.amountMin).toBe('');
    expect(emitted.kind).toBe('liquid');
    expect(emitted.categories).toEqual(['business']);
  });

  it('removing a multi chip drops only that value', async () => {
    const wrapper = mountPanel({
      modelValue: {
        amountMin: '', amountMax: '', kind: '',
        categories: ['business', 'personal'],
      },
    });
    const chip = wrapper
      .findAll('[data-testid="accounting-filter-chip"]')
      .find((c) => c.text().includes('Negocio'));
    await chip.find('button').trigger('click');

    const emitted = wrapper.emitted('update:modelValue').at(-1)[0];
    expect(emitted.categories).toEqual(['personal']);
  });

  it('search chip emits clear-search and reset button emits reset', async () => {
    const wrapper = mountPanel({ searchValue: 'kore' });
    const searchChip = wrapper
      .findAll('[data-testid="accounting-filter-chip"]')
      .find((chip) => chip.text().includes('kore'));
    await searchChip.find('button').trigger('click');
    expect(wrapper.emitted('clear-search')).toHaveLength(1);

    await wrapper.find('[data-testid="accounting-filter-reset"]').trigger('click');
    expect(wrapper.emitted('reset')).toHaveLength(1);
  });

  it('keeps the applied row visible when the panel is closed', () => {
    const wrapper = mountPanel({
      isOpen: false,
      modelValue: { amountMin: '', amountMax: '', kind: 'liquid', categories: [] },
    });
    expect(wrapper.findAll('[data-testid="accounting-filter-chip"]')).toHaveLength(1);
  });
});

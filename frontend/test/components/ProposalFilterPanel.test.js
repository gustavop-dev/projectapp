import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import ProposalFilterPanel from '../../components/proposals/ProposalFilterPanel.vue';

let outsideHandler = null;

jest.mock('@vueuse/core', () => ({
  onClickOutside: jest.fn((_, handler) => {
    outsideHandler = handler;
  }),
}));

const dropdownValueByLabel = {
  Estado: ['sent'],
  'Tipo de proyecto': ['webapp'],
  Mercado: ['b2b'],
  Moneda: ['USD'],
  Idioma: ['en'],
  Activo: ['inactive'],
};

const rangeValueByLabel = {
  Inversión: { min: 1500, max: 3500 },
  'Heat Score': { min: 4, max: 9 },
  Vistas: { min: 3, max: 11 },
  Creación: { min: '2026-02-01', max: '2026-02-28' },
  Actividad: { min: '2026-03-01', max: '2026-03-31' },
};

const stubs = {
  ProposalFilterDropdown: {
    props: ['label'],
    emits: ['update:modelValue'],
    template: `
      <button
        type="button"
        :data-testid="'dropdown-' + label"
        @click="$emit('update:modelValue', dropdownValueByLabel[label])"
      >
        {{ label }}
      </button>
    `,
    computed: {
      dropdownValueByLabel: () => dropdownValueByLabel,
    },
  },
  ProposalFilterRangeDropdown: {
    props: ['label'],
    emits: ['update:minValue', 'update:maxValue'],
    template: `
      <div>
        <button
          type="button"
          :data-testid="'range-min-' + label"
          @click="$emit('update:minValue', rangeValueByLabel[label].min)"
        >
          {{ label }} min
        </button>
        <button
          type="button"
          :data-testid="'range-max-' + label"
          @click="$emit('update:maxValue', rangeValueByLabel[label].max)"
        >
          {{ label }} max
        </button>
      </div>
    `,
    computed: {
      rangeValueByLabel: () => rangeValueByLabel,
    },
  },
};

const createModelValue = (overrides = {}) => ({
  statuses: [],
  projectTypes: [],
  marketTypes: [],
  currencies: [],
  languages: [],
  investmentMin: null,
  investmentMax: null,
  heatScoreMin: null,
  heatScoreMax: null,
  viewCountMin: null,
  viewCountMax: null,
  createdAfter: null,
  createdBefore: null,
  lastActivityAfter: null,
  lastActivityBefore: null,
  isActive: 'all',
  technicalViewed: false,
  ...overrides,
});

function mountPanel(props = {}) {
  outsideHandler = null;
  return mount(ProposalFilterPanel, {
    props: {
      isOpen: true,
      filterCount: 0,
      modelValue: createModelValue(),
      ...props,
    },
    global: { stubs },
  });
}

describe('ProposalFilterPanel', () => {
  it('emits updated statuses when the status dropdown changes', async () => {
    const wrapper = mountPanel();

    await wrapper.get('[data-testid="dropdown-Estado"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [expect.objectContaining({ statuses: ['sent'] })],
    ]);
  });

  it('emits updated scalar and range filters from child controls', async () => {
    const wrapper = mountPanel();

    await wrapper.get('[data-testid="dropdown-Activo"]').trigger('click');
    await wrapper.get('[data-testid="range-min-Inversión"]').trigger('click');
    await wrapper.get('[data-testid="range-max-Actividad"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual(
      expect.objectContaining({ isActive: 'inactive' }),
    );
    expect(wrapper.emitted('update:modelValue')[1][0]).toEqual(
      expect.objectContaining({ investmentMin: 1500 }),
    );
    expect(wrapper.emitted('update:modelValue')[2][0]).toEqual(
      expect.objectContaining({ lastActivityBefore: '2026-03-31' }),
    );
  });

  it('renders active chips for all filter groups', () => {
    const wrapper = mountPanel({
      filterCount: 12,
      modelValue: createModelValue({
        statuses: ['draft'],
        projectTypes: ['webapp'],
        marketTypes: ['b2b'],
        currencies: ['USD'],
        languages: ['en'],
        investmentMin: 1000,
        investmentMax: 5000,
        heatScoreMin: 2,
        heatScoreMax: 8,
        viewCountMin: 1,
        viewCountMax: 9,
        createdAfter: '2026-01-01',
        createdBefore: '2026-01-31',
        lastActivityAfter: '2026-02-01',
        lastActivityBefore: '2026-02-28',
        isActive: 'active',
        technicalViewed: true,
      }),
    });

    expect(wrapper.text()).toContain('Estado: Borrador');
    expect(wrapper.text()).toContain('Tipo: Aplicación Web');
    expect(wrapper.text()).toContain('Mercado: B2B');
    expect(wrapper.text()).toContain('Moneda: USD');
    expect(wrapper.text()).toContain('Idioma: EN');
    expect(wrapper.text()).toContain('Inversión: 1000–5000');
    expect(wrapper.text()).toContain('Heat Score: 2–8 / 10');
    expect(wrapper.text()).toContain('Vistas: 1–9');
    expect(wrapper.text()).toContain('Creación: 2026-01-01 → 2026-01-31');
    expect(wrapper.text()).toContain('Actividad: 2026-02-01 → 2026-02-28');
    expect(wrapper.text()).toContain('Solo activas');
    expect(wrapper.text()).toContain('Det. técnico visto');
  });

  it('renders fallback labels and one-sided ranges for chip text', () => {
    const wrapper = mountPanel({
      modelValue: createModelValue({
        statuses: ['custom-status'],
        projectTypes: ['custom-project'],
        marketTypes: ['custom-market'],
        investmentMin: 1000,
        heatScoreMax: 8,
        createdAfter: '2026-04-01',
        lastActivityBefore: '2026-04-30',
        isActive: 'inactive',
      }),
    });

    expect(wrapper.text()).toContain('Estado: custom-status');
    expect(wrapper.text()).toContain('Tipo: custom-project');
    expect(wrapper.text()).toContain('Mercado: custom-market');
    expect(wrapper.text()).toContain('Inversión: ≥ 1000');
    expect(wrapper.text()).toContain('Heat Score: ≤ 8 / 10');
    expect(wrapper.text()).toContain('Creación: desde 2026-04-01');
    expect(wrapper.text()).toContain('Actividad: hasta 2026-04-30');
    expect(wrapper.text()).toContain('Solo inactivas');
  });

  it('clears a chip by emitting a reset model for that field', async () => {
    const wrapper = mountPanel({
      modelValue: createModelValue({
        statuses: ['draft'],
        investmentMin: 1000,
        investmentMax: 5000,
        technicalViewed: true,
      }),
    });

    await wrapper.get('[data-testid="filter-chip-clear-statuses"]').trigger('click');
    await wrapper.get('[data-testid="filter-chip-clear-investment"]').trigger('click');
    await wrapper.get('[data-testid="filter-chip-clear-technicalViewed"]').trigger('click');

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual(
      expect.objectContaining({ statuses: [] }),
    );
    expect(wrapper.emitted('update:modelValue')[1][0]).toEqual(
      expect.objectContaining({ investmentMin: null, investmentMax: null }),
    );
    expect(wrapper.emitted('update:modelValue')[2][0]).toEqual(
      expect.objectContaining({ technicalViewed: false }),
    );
  });

  it.each([
    ['projectTypes', { projectTypes: ['webapp'] }, { projectTypes: [] }],
    ['marketTypes', { marketTypes: ['b2b'] }, { marketTypes: [] }],
    ['currencies', { currencies: ['USD'] }, { currencies: [] }],
    ['languages', { languages: ['en'] }, { languages: [] }],
    ['heatScore', { heatScoreMin: 1, heatScoreMax: 5 }, { heatScoreMin: null, heatScoreMax: null }],
    ['viewCount', { viewCountMin: 1, viewCountMax: 5 }, { viewCountMin: null, viewCountMax: null }],
    ['createdRange', { createdAfter: '2026-01-01', createdBefore: '2026-01-31' }, { createdAfter: null, createdBefore: null }],
    ['activityRange', { lastActivityAfter: '2026-02-01', lastActivityBefore: '2026-02-28' }, { lastActivityAfter: null, lastActivityBefore: null }],
    ['isActive', { isActive: 'inactive' }, { isActive: 'all' }],
  ])('clears the %s chip with its reset payload', async (chipKey, modelOverrides, expected) => {
    const wrapper = mountPanel({
      modelValue: createModelValue(modelOverrides),
    });

    await wrapper.get(`[data-testid="filter-chip-clear-${chipKey}"]`).trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [expect.objectContaining(expected)],
    ]);
  });

  it('emits reset when the clear-all action is clicked', async () => {
    const wrapper = mountPanel({ filterCount: 1 });

    await wrapper.get('[data-testid="filter-panel-reset"]').trigger('click');

    expect(wrapper.emitted('reset')).toEqual([[]]);
  });

  it('toggles the technical viewed checkbox and closes on outside click', async () => {
    const wrapper = mountPanel({
      modelValue: createModelValue({ technicalViewed: true }),
    });

    await wrapper.get('[data-testid="filter-panel-engagement-toggle"]').trigger('click');
    expect(wrapper.text()).toContain('Solo det. técnico visto');

    await wrapper.get('[data-testid="filter-panel-technical-viewed"]').setValue(false);
    expect(wrapper.emitted('update:modelValue')).toEqual([
      [expect.objectContaining({ technicalViewed: false })],
    ]);

    outsideHandler();
    await nextTick();
    expect(wrapper.find('[data-testid="filter-panel-technical-viewed"]').exists()).toBe(false);
  });
});

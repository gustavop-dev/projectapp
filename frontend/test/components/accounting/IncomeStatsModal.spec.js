import { mount } from '@vue/test-utils';

jest.mock('../../../composables/useChartTheme', () => {
  const { ref } = require('vue');
  return {
    useChartTheme: () => ({
      palette: ref({
        measures: ['#1D4ED8', '#059669', '#B91C1C'],
        categorical: ['#1D4ED8', '#B45309', '#059669', '#7C3AED'],
      }),
      baseOptions: ref({ chart: {}, tooltip: {}, legend: {} }),
    }),
  };
});

import IncomeStatsModal from '~/components/accounting/stats/IncomeStatsModal.vue';

const MONTHLY = [
  {
    period: '2026-01', label: 'Enero 2026',
    expected: '1000000.00', liquid: '800000.00', expenses: '0.00',
  },
  {
    period: '2026-02', label: 'Febrero 2026',
    expected: '0.00', liquid: '0.00', expenses: '0.00',
  },
  {
    period: '2026-03', label: 'Marzo 2026',
    expected: '2000000.00', liquid: '1200000.00', expenses: '0.00',
  },
];

const SUMMARY = {
  year: 2026,
  expected_total: '3000000.00',
  liquid_total: '2000000.00',
};

const STATS = {
  income: {
    liquid: {
      count: 4, total: '2000000.00', avg: '500000.00',
      min: '100000.00', max: '900000.00',
    },
    lost_total: '150000.00',
    top_concepts: [
      { concept: 'Kore v2', total: '1200000.00', count: 2 },
      { concept: 'Hosting Acme', total: '800000.00', count: 2 },
    ],
  },
};

function mountModal(props = {}) {
  return mount(IncomeStatsModal, {
    props: {
      open: true,
      monthly: MONTHLY,
      summary: SUMMARY,
      stats: STATS,
      loading: false,
      ...props,
    },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
        ClientOnly: { template: '<div><slot /></div>' },
        BaseModal: {
          props: ['modelValue', 'size'],
          emits: ['update:modelValue', 'close'],
          template: '<div v-if="modelValue"><slot /></div>',
        },
        apexchart: {
          template: '<div data-testid="apexchart-stub" />',
          props: ['options', 'series', 'type', 'height'],
        },
      },
    },
  });
}

describe('IncomeStatsModal', () => {
  it('renders the evolution tab by default with strip figures from the summary', () => {
    const wrapper = mountModal();

    const strip = wrapper.find('[data-testid="stats-summary-strip"]');
    expect(strip.text()).toContain('Esperado año');
    expect(strip.text()).toContain('$3.000.000 COP');
    expect(strip.text()).toContain('$2.000.000 COP');
    // 2 of 3 months have liquid income: average = (800k + 1.2M) / 2.
    expect(strip.text()).toContain('$1.000.000 COP');
    expect(strip.text()).toContain('2 meses con ingreso');
    // Best month.
    expect(strip.text()).toContain('Marzo 2026');
    // Only the evolution panel is mounted (v-if per tab).
    expect(wrapper.findAll('[data-testid="apexchart-stub"]')).toHaveLength(1);
  });

  it('builds expected vs liquid series from monthly rows', () => {
    const wrapper = mountModal();

    const series = wrapper
      .findComponent('[data-testid="apexchart-stub"]')
      .props('series');
    expect(series).toEqual([
      { name: 'Esperado', data: [1000000, 0, 2000000] },
      { name: 'Líquido', data: [800000, 0, 1200000] },
    ]);
  });

  it('switching to the concepts tab swaps the panel and lists top concepts', async () => {
    const wrapper = mountModal();

    await wrapper.find('[role="tablist"]').findAll('[role="tab"]')[2].trigger('click');

    expect(wrapper.text()).toContain('Registros líquidos');
    expect(wrapper.text()).toContain('Ticket promedio');
    expect(wrapper.text()).toContain('$500.000 COP');
    const chart = wrapper.findComponent('[data-testid="apexchart-stub"]');
    expect(chart.props('options').xaxis.categories).toEqual(['Kore v2', 'Hosting Acme']);
  });

  it('shows the loading skeleton while stats load', () => {
    const wrapper = mountModal({ loading: true, stats: null });

    expect(wrapper.find('[data-testid="stats-modal-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="apexchart-stub"]').exists()).toBe(false);
  });
});

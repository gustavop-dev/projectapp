import { mount } from '@vue/test-utils';

jest.mock('../../../composables/useChartTheme', () => {
  const { ref } = require('vue');
  return {
    useChartTheme: () => ({
      palette: ref({
        measures: ['#1D4ED8', '#059669', '#B91C1C'],
        categorical: ['#1D4ED8', '#B45309', '#059669', '#7C3AED'],
        text: '#6B7280',
        grid: '#F3F4F6',
      }),
      baseOptions: ref({ chart: {}, tooltip: {}, legend: {} }),
    }),
  };
});

import UtilityStatsPanel from '~/components/accounting/stats/UtilityStatsPanel.vue';

const MONTHLY = [
  {
    period: '2026-01', label: 'Enero 2026',
    expected_utility: '800000.00', utility: '600000.00', liquid: '1000000.00',
  },
  {
    period: '2026-02', label: 'Febrero 2026',
    expected_utility: '400000.00', utility: '200000.00', liquid: '500000.00',
  },
];

function mountPanel() {
  return mount(UtilityStatsPanel, {
    props: {
      monthly: MONTHLY,
      summary: {
        year: 2026,
        expected_utility: '1200000.00',
        liquid_utility: '800000.00',
        difference: '-400000.00',
        liquid_total: '1500000.00',
        expenses_total: '700000.00',
      },
      partners: {
        gustavo: { expected: 600000, liquid: 400000, expenses: 100000, net: 300000 },
      },
    },
    global: {
      stubs: {
        ClientOnly: { template: '<div><slot /></div>' },
        NuxtLink: { template: '<a><slot /></a>' },
        LazyApexChart: {
          template: '<div data-testid="apexchart-stub" />',
          props: ['options', 'series', 'type', 'height'],
        },
      },
    },
  });
}

describe('UtilityStatsPanel', () => {
  it('starts open on the evolution tab', () => {
    const wrapper = mountPanel();

    expect(wrapper.get('[data-testid="utility-stats-toggle"]').attributes('aria-expanded'))
      .toBe('true');
    expect(wrapper.text()).toContain('Utilidad esperada año');
    expect(wrapper.find('[data-testid="apexchart-stub"]').exists()).toBe(true);
  });

  it('collapses the analytics content', async () => {
    const wrapper = mountPanel();

    await wrapper.get('[data-testid="utility-stats-toggle"]').trigger('click');

    expect(wrapper.get('[data-testid="utility-stats-toggle"]').attributes('aria-expanded'))
      .toBe('false');
    expect(wrapper.get('#utility-stats-content').attributes('aria-hidden')).toBe('true');
  });

  it('shows the yearly margin on the margin tab', async () => {
    const wrapper = mountPanel();

    await wrapper.findAll('[role="tab"]')[1].trigger('click');

    expect(wrapper.text()).toContain('53.3%');
  });
});

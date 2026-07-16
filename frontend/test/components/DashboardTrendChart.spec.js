import { mount } from '@vue/test-utils';

jest.mock('../../composables/useChartTheme', () => ({
  useChartTheme: () => ({
    palette: {
      value: { measures: ['#1D4ED8', '#059669', '#B91C1C'], categorical: [] },
    },
    baseOptions: { value: { chart: {} } },
  }),
}));

import DashboardTrendChart from '../../components/panel/dashboard/DashboardTrendChart.vue';

const GLOBAL = {
  stubs: {
    ClientOnly: { template: '<div><slot /></div>' },
    apexchart: {
      template: '<div data-testid="apexchart-stub" />',
      props: ['options', 'series', 'type', 'height'],
    },
  },
};

function mountChart(trend) {
  return mount(DashboardTrendChart, { props: { trend }, global: GLOBAL });
}

describe('DashboardTrendChart', () => {
  it('shows the empty state when the trend has no activity', () => {
    const wrapper = mountChart([
      { month: '2026-01-01', sent: 0, accepted: 0, rejected: 0 },
    ]);

    expect(wrapper.text()).toContain('Sin propuestas en los últimos meses');
    expect(wrapper.find('[data-testid="apexchart-stub"]').exists()).toBe(false);
  });

  it('builds stacked series clamping in-progress at zero', () => {
    const wrapper = mountChart([
      { month: '2026-05-01', sent: 3, accepted: 1, rejected: 1 },
      { month: '2026-06-01', sent: 1, accepted: 2, rejected: 0 },
    ]);

    const series = wrapper
      .findComponent('[data-testid="apexchart-stub"]')
      .props('series');
    expect(series).toEqual([
      { name: 'Aceptadas', data: [1, 2] },
      { name: 'Rechazadas', data: [1, 0] },
      { name: 'En curso', data: [1, 0] },
    ]);
  });

  it('renders an empty category label for rows without a month', () => {
    const wrapper = mountChart([
      { month: null, sent: 2, accepted: 1, rejected: 0 },
    ]);

    const options = wrapper
      .findComponent('[data-testid="apexchart-stub"]')
      .props('options');
    expect(options.xaxis.categories).toEqual(['']);
  });
});

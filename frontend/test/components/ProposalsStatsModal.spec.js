import { mount, flushPromises } from '@vue/test-utils';

jest.mock('../../composables/useChartTheme', () => {
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

const mockNotifyError = jest.fn();
jest.mock('../../composables/usePanelNotify', () => ({
  usePanelNotify: () => ({ error: mockNotifyError, success: jest.fn() }),
}));

const mockFetchProposalDashboard = jest.fn();
jest.mock('../../stores/proposals', () => ({
  useProposalStore: () => ({ fetchProposalDashboard: mockFetchProposalDashboard }),
}));

import ProposalsStatsModal from '~/components/panel/dashboard/ProposalsStatsModal.vue';

const DASHBOARD = {
  total_proposals: 12,
  by_status: { draft: 2, sent: 3, viewed: 2, accepted: 3, rejected: 2 },
  conversion_rate: 60,
  pipeline_value: 25000000,
  pipeline_count: 5,
  avg_value_by_status: { accepted: 9000000, rejected: 4000000, sent: 0 },
  monthly_trend: [
    { month: '2026-05-01', sent: 3, accepted: 1, rejected: 1 },
    { month: '2026-06-01', sent: 2, accepted: 0, rejected: 0 },
  ],
};

function mountModal(props = {}) {
  const wrapper = mount(ProposalsStatsModal, {
    props: { open: true, ...props },
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
  return { wrapper };
}

describe('ProposalsStatsModal', () => {
  beforeEach(() => {
    mockNotifyError.mockClear();
    mockFetchProposalDashboard.mockReset();
    mockFetchProposalDashboard.mockResolvedValue({ success: true, data: DASHBOARD });
  });

  it('fetches the proposals dashboard once on first open only', async () => {
    const { wrapper } = mountModal();
    await flushPromises();

    expect(mockFetchProposalDashboard).toHaveBeenCalledTimes(1);

    await wrapper.setProps({ open: false });
    await wrapper.setProps({ open: true });
    await flushPromises();
    expect(mockFetchProposalDashboard).toHaveBeenCalledTimes(1);
  });

  it('does not fetch while closed', async () => {
    mountModal({ open: false });
    await flushPromises();

    expect(mockFetchProposalDashboard).not.toHaveBeenCalled();
  });

  it('renders overview strip figures after loading', async () => {
    const { wrapper } = mountModal();
    await flushPromises();

    const strip = wrapper.find('[data-testid="stats-summary-strip"]');
    expect(strip.text()).toContain('12');
    expect(strip.text()).toContain('$25.000.000 COP');
    expect(strip.text()).toContain('5 en curso');
    expect(strip.text()).toContain('60%');
  });

  it('computes monthly conversion with null months when no terminals', async () => {
    const { wrapper } = mountModal();
    await flushPromises();

    await wrapper.find('[role="tablist"]').findAll('[role="tab"]')[3].trigger('click');

    const charts = wrapper.findAllComponents('[data-testid="apexchart-stub"]');
    const line = charts.find((chart) => chart.props('type') === 'line');
    // May 2026: 1 accepted / 2 terminal = 50%; June: no terminals → null.
    expect(line.props('series')).toEqual([{ name: '% conversión', data: [50, null] }]);
  });
});

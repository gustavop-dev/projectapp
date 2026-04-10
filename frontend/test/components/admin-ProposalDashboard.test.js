import { mount } from '@vue/test-utils';

const mockFetchDashboard = jest.fn().mockResolvedValue({ success: true, data: { total_proposals: 5 } });
global.useProposalStore = jest.fn(() => ({
  fetchProposalDashboard: mockFetchDashboard,
}));

global.useTooltipTexts = jest.fn(() => ({
  dashboard: {
    conversionRate: 'Tasa de conversión total',
    totalProposals: 'Total de propuestas',
  },
}));

import ProposalDashboard from '../../components/BusinessProposal/admin/ProposalDashboard.vue';

function mountProposalDashboard(props = {}) {
  return mount(ProposalDashboard, {
    props,
    global: {
      stubs: {
        QuestionMarkCircleIcon: { template: '<span class="q-icon" />' },
        UiTooltip: { template: '<div><slot /><slot name="trigger" /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ProposalDashboard', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders the toggle button', () => {
    const wrapper = mountProposalDashboard();

    expect(wrapper.find('button').exists()).toBe(true);
  });

  it('shows "Mostrar Dashboard KPI" when collapsed', () => {
    const wrapper = mountProposalDashboard();

    expect(wrapper.text()).toContain('Mostrar Dashboard KPI');
  });

  it('shows "Ocultar Dashboard" after toggle button is clicked', async () => {
    const wrapper = mountProposalDashboard();

    await wrapper.find('button').trigger('click');

    expect(wrapper.text()).toContain('Ocultar Dashboard');
  });

  it('calls fetchProposalDashboard when opened', async () => {
    mockFetchDashboard.mockClear();
    const wrapper = mountProposalDashboard();

    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();

    expect(mockFetchDashboard).toHaveBeenCalled();
  });
});

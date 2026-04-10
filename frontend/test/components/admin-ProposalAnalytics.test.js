import { mount } from '@vue/test-utils';

global.useProposalStore = jest.fn(() => ({
  fetchProposalAnalytics: jest.fn().mockResolvedValue({ success: false, data: null }),
}));

global.useTooltipTexts = jest.fn(() => ({
  analytics: {
    engagementScore: 'Puntaje de engagement',
    summary: 'Resumen de visitas y actividad',
  },
}));

import ProposalAnalytics from '../../components/BusinessProposal/admin/ProposalAnalytics.vue';

function mountProposalAnalytics(props = {}) {
  return mount(ProposalAnalytics, {
    props: {
      proposalId: 42,
      proposal: null,
      ...props,
    },
    global: {
      stubs: {
        QuestionMarkCircleIcon: { template: '<span class="q-icon" />' },
        UiTooltip: { template: '<div><slot /><slot name="trigger" /></div>' },
      },
    },
  });
}

describe('ProposalAnalytics', () => {
  it('shows loading state on mount', () => {
    const wrapper = mountProposalAnalytics();

    // loading is true before the async fetch resolves
    expect(wrapper.text()).toContain('Cargando analytics');
  });

  it('renders the component wrapper', () => {
    const wrapper = mountProposalAnalytics();

    expect(wrapper.find('div').exists()).toBe(true);
  });

  it('shows no-data state after fetch returns no data', async () => {
    const wrapper = mountProposalAnalytics();

    // Wait for onMounted async fetch to complete
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No hay datos de analytics');
  });

  it('passes proposalId to the analytics fetch on mount', async () => {
    const mockFetch = jest.fn().mockResolvedValue({ success: false, data: null });
    global.useProposalStore = jest.fn(() => ({ fetchProposalAnalytics: mockFetch }));

    mountProposalAnalytics({ proposalId: 99 });

    expect(mockFetch).toHaveBeenCalledWith(99);
  });
});

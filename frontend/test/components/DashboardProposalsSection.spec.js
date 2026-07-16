import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);

import DashboardProposalsSection from '../../components/panel/dashboard/DashboardProposalsSection.vue';

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to" v-bind="$attrs"><slot /></a>', props: ['to'] },
    DashboardTrendChart: true,
  },
};

function makeProposals(overrides = {}) {
  return {
    conversion_rate: 60,
    total_proposals: 12,
    by_status: { draft: 2, accepted: 1 },
    monthly_trend: [],
    recent: [],
    ...overrides,
  };
}

function mountSection(proposals) {
  return mount(DashboardProposalsSection, {
    props: { proposals },
    global: GLOBAL,
  });
}

describe('DashboardProposalsSection', () => {
  it('hides the section when proposals is null', () => {
    const wrapper = mountSection(null);

    expect(
      wrapper.find('[data-testid="dashboard-proposals-section"]').exists(),
    ).toBe(false);
  });

  it('renders pills only for statuses with a positive count', () => {
    const wrapper = mountSection(
      makeProposals({ by_status: { draft: 2, sent: 0, accepted: 1 } }),
    );

    const pills = wrapper.find('[data-testid="dashboard-status-pills"]');
    expect(pills.text()).toContain('Borrador: 2');
    expect(pills.text()).toContain('Aceptada: 1');
    expect(pills.text()).not.toContain('Enviada');
  });

  it('links each recent proposal to its edit page with its status label', () => {
    const wrapper = mountSection(
      makeProposals({
        recent: [
          { id: 7, title: 'Web Kore', client_name: 'Kore', status: 'negotiating' },
        ],
      }),
    );

    const link = wrapper.find('a[href="/panel/proposals/7/edit"]');
    expect(link.exists()).toBe(true);
    expect(link.text()).toContain('Web Kore');
    expect(link.text()).toContain('Negociando');
  });

  it('shows the empty state when there are no recent proposals', () => {
    const wrapper = mountSection(makeProposals());

    expect(wrapper.text()).toContain('Aún no hay propuestas');
  });

  it('falls back to the raw status when the label is unknown', () => {
    const wrapper = mountSection(
      makeProposals({
        recent: [
          { id: 9, title: 'X', client_name: 'Y', status: 'archived_custom' },
        ],
      }),
    );

    expect(wrapper.text()).toContain('archived_custom');
  });
});

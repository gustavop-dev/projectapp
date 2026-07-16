import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);

import DashboardFinanceSection from '../../components/panel/dashboard/DashboardFinanceSection.vue';

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to" v-bind="$attrs"><slot /></a>', props: ['to'] },
    AccountingHeroKpi: true,
  },
};

function makeFinance(overrides = {}) {
  return {
    year: 2026,
    liquid_utility: '1000000.00',
    monthly: [],
    pocket_balance: '500000.00',
    card_debt: { total: '200000.00', utilization_pct: 35 },
    expected_current_month: { total: '0.00', label: 'julio' },
    recurring_monthly_cost: '80000.00',
    hostings: { active_count: 3, monthly_income: '150000.00' },
    ...overrides,
  };
}

function mountSection(finance) {
  return mount(DashboardFinanceSection, {
    props: { finance },
    global: GLOBAL,
  });
}

describe('DashboardFinanceSection', () => {
  it('hides the section when finance is null', () => {
    const wrapper = mountSection(null);

    expect(
      wrapper.find('[data-testid="dashboard-finance-section"]').exists(),
    ).toBe(false);
  });

  it('renders the pocket balance as es-CO currency', async () => {
    const wrapper = mountSection(makeFinance());
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('$500.000');
  });

  it('shows the card utilization percentage as subtitle', () => {
    const wrapper = mountSection(makeFinance());

    expect(wrapper.text()).toContain('35% del cupo');
  });

  it('omits the utilization subtitle when the percentage is unknown', () => {
    const wrapper = mountSection(
      makeFinance({ card_debt: { total: '0.00', utilization_pct: null } }),
    );

    expect(wrapper.text()).not.toContain('del cupo');
  });

  it('shows hosting monthly income only when it is positive', () => {
    const withIncome = mountSection(makeFinance());
    const withoutIncome = mountSection(
      makeFinance({ hostings: { active_count: 1, monthly_income: '0.00' } }),
    );

    expect(withIncome.text()).toContain('/mes');
    expect(withoutIncome.text()).not.toContain('/mes');
  });
});

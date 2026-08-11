import { mount } from '@vue/test-utils';

jest.mock('../../../composables/useChartTheme', () => {
  const { ref } = require('vue');
  return {
    useChartTheme: () => ({
      palette: ref({
        measures: ['#1D4ED8', '#059669', '#B91C1C'],
        categorical: ['#1D4ED8', '#B45309', '#059669', '#7C3AED'],
        text: '#6B7280',
      }),
      baseOptions: ref({ chart: {}, tooltip: {}, legend: {} }),
    }),
  };
});

import RecurringChartsModal from '~/components/accounting/stats/RecurringChartsModal.vue';

const CATEGORIES = [
  { id: 1, name: 'Suscripciones de IA' },
  { id: 2, name: 'Anuncios / publicidad' },
];

function payment(overrides = {}) {
  return {
    id: 1,
    name: 'Pago',
    price: '10000.00',
    currency: 'COP',
    monthly_price: '10000.00',
    monthly_cop_cost: '10000.00',
    payment_method: 'credit_card',
    payment_method_label: 'T.C',
    frequency: 'monthly',
    frequency_label: 'Mensual',
    cost_type: 'fixed',
    cost_type_label: 'Fijo',
    billing_day: 8,
    category: 1,
    is_active: true,
    ...overrides,
  };
}

const ROWS = [
  payment({ id: 1, name: 'Claude', category: 1, currency: 'USD', price: '200.00', monthly_price: '200.00', monthly_cop_cost: '800000.00' }),
  payment({ id: 2, name: 'Google Ads', category: 2, monthly_cop_cost: '1200000.00', billing_day: null }),
  payment({ id: 3, name: 'Netflix', category: 1, monthly_cop_cost: '39800.00' }),
];

function mountModal(props = {}) {
  return mount(RecurringChartsModal, {
    props: { open: true, rows: ROWS, categories: CATEGORIES, ...props },
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

function tabs(wrapper) {
  return wrapper.find('[role="tablist"]').findAll('[role="tab"]');
}

describe('RecurringChartsModal', () => {
  it('opens on the category tab with every category priced and weighted in the legend', () => {
    const wrapper = mountModal();

    const legend = wrapper.find('[data-testid="recurring-chart-legend"]');
    expect(legend.text()).toContain('Suscripciones de IA');
    expect(legend.text()).toContain('$839.800 COP');
    expect(legend.text()).toContain('41,2%');
    expect(legend.text()).toContain('$1.200.000 COP');
    expect(legend.text()).toContain('58,8%');
  });

  it('leaves inactive payments out of the distribution until asked for them', async () => {
    const wrapper = mountModal({
      rows: [
        payment({ id: 1, category: 1, monthly_cop_cost: '800000.00' }),
        payment({ id: 2, category: 2, monthly_cop_cost: '200000.00', is_active: false }),
      ],
    });
    expect(wrapper.find('[data-testid="recurring-chart-legend"]').text())
      .not.toContain('Anuncios / publicidad');

    await wrapper.find('[role="switch"]').trigger('click');

    const legend = wrapper.find('[data-testid="recurring-chart-legend"]');
    expect(legend.text()).toContain('Anuncios / publicidad');
    expect(legend.text()).toContain('20%');
  });

  it('spells out the filters inherited from the table and offers a way out', async () => {
    const wrapper = mountModal({ inheritedChips: ['Moneda: USD'] });

    expect(wrapper.find('[data-testid="recurring-charts-chip"]').text()).toBe('Moneda: USD');

    await wrapper.find('[data-testid="recurring-charts-clear-filters"]').trigger('click');

    expect(wrapper.emitted('clear-filters')).toHaveLength(1);
  });

  it('drilling into a category from the legend narrows every chart to its payments', async () => {
    const wrapper = mountModal();

    await wrapper.find('[data-testid="recurring-chart-legend-item-1"]').trigger('click');
    await tabs(wrapper)[1].trigger('click');

    const chart = wrapper.findComponent('[data-testid="apexchart-stub"]');
    expect(chart.props('options').xaxis.categories).toEqual(['Claude', 'Netflix']);
  });

  it('ranks the items tab by monthly cost and colors each bar by its category', async () => {
    const wrapper = mountModal();

    await tabs(wrapper)[1].trigger('click');

    const options = wrapper.findComponent('[data-testid="apexchart-stub"]').props('options');
    expect(options.xaxis.categories).toEqual(['Google Ads', 'Claude', 'Netflix']);
    expect(options.colors).toEqual(['#B45309', '#1D4ED8', '#1D4ED8']);
  });

  it('breaks the composition down by currency, method and cost type at once', async () => {
    const wrapper = mountModal();

    await tabs(wrapper)[2].trigger('click');

    expect(wrapper.text()).toContain('Expuesto al dólar');
    expect(wrapper.text()).toContain('$800.000 COP');
    const chart = wrapper.findComponent('[data-testid="apexchart-stub"]');
    expect(chart.props('options').xaxis.categories).toEqual(['Moneda', 'Método', 'Tipo']);
  });

  it('calls out the spend with no billing day instead of hiding it off the axis', async () => {
    const wrapper = mountModal();

    await tabs(wrapper)[3].trigger('click');

    const callout = wrapper.find('[data-testid="recurring-charts-no-day"]');
    expect(callout.text()).toContain('$1.200.000 COP');
    expect(callout.text()).toContain('58,8%');
    expect(callout.text()).toContain('Google Ads');
  });

  it('explains an empty slice rather than drawing a blank donut', () => {
    const wrapper = mountModal({ rows: [payment({ is_active: false })] });

    expect(wrapper.text()).toContain('Nada que graficar con estos filtros');
    expect(wrapper.text()).toContain('Incluir inactivos');
  });
});

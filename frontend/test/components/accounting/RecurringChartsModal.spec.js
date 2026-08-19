import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

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
        LazyApexChart: {
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

function donut(wrapper) {
  return wrapper.findComponent('[data-testid="apexchart-stub"]');
}

/** Drill into a category the way the operator does: clicking its legend row. */
async function drillInto(wrapper, categoryId) {
  await wrapper.find(`[data-testid="recurring-chart-legend-item-${categoryId}"]`).trigger('click');
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

describe('RecurringChartsModal — drilling into one category', () => {
  it('splits the donut by the payments of the category, not into one 100% slice', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 1);

    // The reported bug: the donut used to keep grouping by category, so the
    // only category left became a single slice worth all of it.
    expect(donut(wrapper).props('options').labels).toEqual(['Claude', 'Netflix']);
    expect(donut(wrapper).props('series')).toEqual([800000, 39800]);
  });

  it('swaps the legend to the payments of that category', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 1);

    const legend = wrapper.find('[data-testid="recurring-chart-legend"]');
    expect(legend.text()).toContain('Claude');
    expect(legend.text()).toContain('Netflix');
    expect(legend.text()).not.toContain('Anuncios / publicidad');
  });

  it('weighs each payment inside its category and over the general total', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 1);

    // Claude is 800.000 of the category's 839.800, and of everything's 2.039.800.
    const legend = wrapper.find('[data-testid="recurring-chart-legend"]');
    expect(legend.text()).toContain('95,3%');
    expect(legend.text()).toContain('39,2%');
    expect(legend.text()).toContain('del total general');
  });

  it('names the category and the base its percentages are read against', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 1);

    const header = wrapper.find('[data-testid="recurring-charts-drill-header"]');
    expect(header.text()).toContain('Suscripciones de IA');
    expect(header.text()).toContain('$839.800 COP');
    expect(header.text()).toContain('son sobre esta categoría');
    expect(donut(wrapper).props('options').plotOptions.pie.donut.labels.total.label)
      .toBe('Total categoría');
  });

  it('colors the payments by their rank, never by the category they share', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 1);

    // Both are category 1: painted by category they would be the same blue,
    // and the donut would be one flat color again.
    expect(donut(wrapper).props('options').colors).toEqual(['#1D4ED8', '#B45309']);
  });

  it('starts the ramp at the drilled category own hue, so the drill reads as a zoom', async () => {
    const wrapper = mountModal({
      rows: [
        payment({ id: 1, name: 'Google Ads', category: 2, monthly_cop_cost: '900000.00' }),
        payment({ id: 2, name: 'Meta Ads', category: 2, monthly_cop_cost: '300000.00' }),
      ],
    });

    await drillInto(wrapper, 2);

    // Category 2 wears the second slot in the general view; its biggest payment
    // inherits it instead of restarting the ramp at blue.
    expect(donut(wrapper).props('options').colors).toEqual(['#B45309', '#059669']);
  });

  it('returns to the general view in one click, without reopening the modal', async () => {
    const wrapper = mountModal();
    await drillInto(wrapper, 1);

    await wrapper.find('[data-testid="recurring-charts-back"]').trigger('click');

    expect(wrapper.find('[data-testid="recurring-charts-drill-header"]').exists()).toBe(false);
    const legend = wrapper.find('[data-testid="recurring-chart-legend"]');
    expect(legend.text()).toContain('Suscripciones de IA');
    expect(legend.text()).toContain('Anuncios / publicidad');
  });

  it('names the lone payment when a category has only one, so 100% reads as real', async () => {
    const wrapper = mountModal();

    await drillInto(wrapper, 2);

    expect(wrapper.find('[data-testid="recurring-charts-single-item"]').text())
      .toContain('Google Ads');
  });

  it('does not let clicking a payment toggle the category that shares its id', async () => {
    const wrapper = mountModal();
    await drillInto(wrapper, 1);

    // Claude is payment id 1 inside category id 1: the ids collide.
    // quality: allow-implementation-coupling (the chart is stubbed, so a slice
    // click only exists as ApexCharts' callback — there is no DOM to click)
    donut(wrapper).vm.$emit('data-point-selection', {}, {}, { dataPointIndex: 0 });
    await nextTick();

    expect(wrapper.find('[data-testid="recurring-charts-drill-header"]').exists()).toBe(true);
    expect(donut(wrapper).props('options').labels).toEqual(['Claude', 'Netflix']);
  });

  it('keeps the way back when the drilled category has nothing left to show', async () => {
    const wrapper = mountModal({
      rows: [
        payment({ id: 1, category: 1, monthly_cop_cost: '800000.00' }),
        payment({ id: 2, category: 2, monthly_cop_cost: '200000.00', is_active: false }),
      ],
    });

    // Only reachable through the select: an all-inactive category has no
    // legend row to click.
    await wrapper.find('[data-testid="recurring-charts-category"]').setValue('2');

    expect(wrapper.find('[data-testid="recurring-charts-back"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Los pagos de esta categoría están inactivos');
  });

  it('drills into the uncategorized bucket instead of emptying the modal', async () => {
    const wrapper = mountModal({
      rows: [
        payment({ id: 1, name: 'Claude', category: 1, monthly_cop_cost: '800000.00' }),
        payment({ id: 2, name: 'Dominio suelto', category: null, monthly_cop_cost: '4499.00' }),
      ],
    });

    await drillInto(wrapper, 'uncategorized');

    expect(donut(wrapper).props('options').labels).toEqual(['Dominio suelto']);
    expect(wrapper.find('[data-testid="recurring-charts-drill-header"]').text())
      .toContain('Sin categoría');
  });
});

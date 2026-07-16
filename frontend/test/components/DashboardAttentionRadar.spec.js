import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);

import DashboardAttentionRadar from '../../components/panel/dashboard/DashboardAttentionRadar.vue';

const GLOBAL = {
  stubs: {
    NuxtLink: { template: '<a :href="to" v-bind="$attrs"><slot /></a>', props: ['to'] },
  },
};

function mountRadar(items = []) {
  return mount(DashboardAttentionRadar, { props: { items }, global: GLOBAL });
}

describe('DashboardAttentionRadar', () => {
  it('shows the positive empty state when there are no items', () => {
    const wrapper = mountRadar([]);

    expect(wrapper.find('[data-testid="attention-radar-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Nada requiere tu atención');
  });

  it('maps item types to Spanish copy and module label', () => {
    const wrapper = mountRadar([
      { type: 'documents_overdue', severity: 'danger', count: 2, meta: {} },
      { type: 'tasks_overdue', severity: 'warning', count: 3, meta: { high_priority: 1 } },
    ]);

    const docs = wrapper.find('[data-testid="attention-item-documents_overdue"]');
    expect(docs.text()).toContain('2 cuentas de cobro vencidas');
    expect(docs.text()).toContain('Documentos');

    const tasks = wrapper.find('[data-testid="attention-item-tasks_overdue"]');
    expect(tasks.text()).toContain('3 tareas vencidas');
    expect(tasks.text()).toContain('1 de alta prioridad');
  });

  it('uses singular copy when count is one', () => {
    const wrapper = mountRadar([
      { type: 'emails_failed', severity: 'danger', count: 1, meta: {} },
    ]);

    expect(wrapper.text()).toContain('1 email fallido');
  });

  it('links each item to its module route', () => {
    const wrapper = mountRadar([
      { type: 'proposals_stale', severity: 'warning', count: 1, meta: { days: 7 } },
      { type: 'recurring_due', severity: 'info', count: 2, meta: { next_days: 0 } },
    ]);

    const links = wrapper.findAll('a');
    expect(links[0].attributes('href')).toBe('/panel/proposals');
    expect(links[1].attributes('href')).toBe('/panel/accounting/recurring');
    expect(links[1].text()).toContain('vence hoy');
  });

  it('accents items with the severity status tokens', () => {
    const wrapper = mountRadar([
      { type: 'documents_overdue', severity: 'danger', count: 1, meta: {} },
    ]);

    expect(
      wrapper.find('[data-testid="attention-item-documents_overdue"]').classes(),
    ).toContain('border-l-danger-strong');
  });
});

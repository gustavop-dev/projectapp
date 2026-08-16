import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);

import DashboardOperationsSection from '../../components/panel/dashboard/DashboardOperationsSection.vue';

// Registrado como componente y no como stub: las tarjetas de esta sección
// llevan `to`, así que DashboardStatTile las renderiza resolviendo NuxtLink con
// `resolveComponent` (un string en `:is` no resuelve un auto-import de Nuxt), y
// `resolveComponent` sólo encuentra lo que está registrado. Como stub, la
// tarjeta se reemplazaba por una vacía y se perdía todo su contenido.
const GLOBAL = {
  components: {
    NuxtLink: { name: 'NuxtLink', props: ['to'], template: '<a :href="to" v-bind="$attrs"><slot /></a>' },
  },
};

function makeOperations(overrides = {}) {
  return {
    tasks: { open: 5, overdue: 0, overdue_high: 0, blocked: 0 },
    documents: {
      collection_accounts: {
        outstanding_total: '100000.00',
        issued_count: 2,
        overdue_issued: 0,
      },
    },
    emails: {
      success_rate: 97.5,
      total_30d: 40,
      failed_count: 1,
      daily_trend: [],
    },
    diagnostics: { active_pipeline: 2, accepted_value: '0.00' },
    hour_packages: { active_count: 4 },
    ...overrides,
  };
}

function mountSection(operations) {
  return mount(DashboardOperationsSection, {
    props: { operations },
    global: GLOBAL,
  });
}

describe('DashboardOperationsSection', () => {
  it('hides the section when operations is null', () => {
    const wrapper = mountSection(null);

    expect(
      wrapper.find('[data-testid="dashboard-operations-section"]').exists(),
    ).toBe(false);
  });

  it('shows the empty state when every indicator is zero', () => {
    const wrapper = mountSection({});

    expect(wrapper.text()).toContain('Sin actividad operativa aún');
  });

  it('summarizes overdue and blocked tasks in the tile subtitle', () => {
    const wrapper = mountSection(
      makeOperations({
        tasks: { open: 7, overdue: 2, overdue_high: 0, blocked: 1 },
      }),
    );

    expect(wrapper.text()).toContain('2 vencidas · 1 bloqueadas');
  });

  it('falls back to "sin vencidas" when no task is overdue', () => {
    const wrapper = mountSection(makeOperations());

    expect(wrapper.text()).toContain('sin vencidas');
  });

  it('reports failed emails out of the 30-day total', () => {
    const wrapper = mountSection(
      makeOperations({
        emails: {
          success_rate: 85,
          total_30d: 40,
          failed_count: 6,
          daily_trend: [],
        },
      }),
    );

    expect(wrapper.text()).toContain('6 fallidos de 40');
  });

  it('uses singular copy for one issued collection account with overdue', () => {
    const wrapper = mountSection(
      makeOperations({
        documents: {
          collection_accounts: {
            outstanding_total: '50000.00',
            issued_count: 1,
            overdue_issued: 1,
          },
        },
      }),
    );

    expect(wrapper.text()).toContain('1 emitida · 1 vencida');
  });

  it('shows the accepted diagnostics value as money when positive', () => {
    const wrapper = mountSection(
      makeOperations({
        diagnostics: { active_pipeline: 3, accepted_value: '3000000.00' },
      }),
    );

    expect(wrapper.text()).toContain('$3.000.000 aceptado');
  });
});

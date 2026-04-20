import { mount } from '@vue/test-utils';

global.useTooltipTexts = jest.fn(() => ({
  analytics: {
    engagementScore: 'Puntaje de engagement',
    summary: 'Resumen de visitas y actividad',
    comparison: 'Comparación con el promedio global',
    funnel: 'Embudo de secciones',
    devices: 'Dispositivos desde los que se accedió',
    sessionHistory: 'Historial de sesiones',
    sectionEngagement: 'Tiempo por sección',
    skippedSections: 'Secciones no visitadas',
  },
}));

import DiagnosticAnalytics from '../../components/WebAppDiagnostic/admin/DiagnosticAnalytics.vue';

const emptyLoader = jest.fn().mockResolvedValue({ success: false, data: null });

function mountComponent(props = {}) {
  return mount(DiagnosticAnalytics, {
    props: {
      diagnosticId: 42,
      loader: emptyLoader,
      diagnostic: null,
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

describe('DiagnosticAnalytics', () => {
  it('shows loading state on mount', () => {
    const wrapper = mountComponent();

    expect(wrapper.text()).toContain('Cargando analytics');
  });

  it('shows no-data state when loader returns no data', async () => {
    const wrapper = mountComponent();

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('No hay datos de analytics');
  });

  it('calls the loader with no arguments on mount', () => {
    const mockLoader = jest.fn().mockResolvedValue({ success: false, data: null });
    mountComponent({ loader: mockLoader });

    expect(mockLoader).toHaveBeenCalledTimes(1);
  });

  it('re-fetches when diagnosticId prop changes', async () => {
    const mockLoader = jest.fn().mockResolvedValue({ success: false, data: null });
    const wrapper = mountComponent({ loader: mockLoader });

    await wrapper.setProps({ diagnosticId: 99 });

    expect(mockLoader).toHaveBeenCalledTimes(2);
  });
});

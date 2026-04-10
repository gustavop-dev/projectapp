import { mount } from '@vue/test-utils';
import MetricsManual from '../../components/BusinessProposal/admin/MetricsManual.vue';

function mountMetricsManual(props = {}) {
  return mount(MetricsManual, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('MetricsManual', () => {
  it('renders the floating trigger button', () => {
    const wrapper = mountMetricsManual();

    const btn = wrapper.find('button[title="Manual de métricas"]');
    expect(btn.exists()).toBe(true);
  });

  it('panel is hidden initially', () => {
    const wrapper = mountMetricsManual();

    expect(wrapper.text()).not.toContain('Manual de Métricas');
  });

  it('shows metrics panel after clicking the trigger button', async () => {
    const wrapper = mountMetricsManual();

    await wrapper.find('button[title="Manual de métricas"]').trigger('click');

    expect(wrapper.text()).toContain('Manual de Métricas');
  });

  it('renders metric items after opening', async () => {
    const wrapper = mountMetricsManual();

    await wrapper.find('button[title="Manual de métricas"]').trigger('click');

    expect(wrapper.text()).toContain('Tasa de conversión');
  });

  it('shows search input after opening', async () => {
    const wrapper = mountMetricsManual();

    await wrapper.find('button[title="Manual de métricas"]').trigger('click');

    expect(wrapper.find('input[placeholder="Buscar métrica..."]').exists()).toBe(true);
  });
});

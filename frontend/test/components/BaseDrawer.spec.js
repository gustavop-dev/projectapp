import { mount } from '@vue/test-utils';
import BaseDrawer from '../../components/base/BaseDrawer.vue';

function mountDrawer(props = {}, slots = { default: '<p>Contenido del cajón</p>' }) {
  document.body.innerHTML = '<div id="app"></div>';
  return mount(BaseDrawer, {
    props: { modelValue: true, title: 'Filtros', ...props },
    slots,
    attachTo: document.body,
    global: {
      stubs: { NuxtLink: { template: '<a><slot /></a>' } },
    },
  });
}

describe('BaseDrawer', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('presents its title and content as a modal dialog', () => {
    const wrapper = mountDrawer();
    const dialog = document.body.querySelector('[role="dialog"]');

    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.textContent).toContain('Filtros');
    expect(dialog.textContent).toContain('Contenido del cajón');
    wrapper.unmount();
  });

  it('asks the parent to close from its close button', async () => {
    const wrapper = mountDrawer();

    document.body.querySelector('button[aria-label="Cerrar"]').click();
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    expect(wrapper.emitted('close')).toHaveLength(1);
    wrapper.unmount();
  });

  it('asks the parent to close when Escape is pressed', async () => {
    const wrapper = mountDrawer();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
    wrapper.unmount();
  });
});

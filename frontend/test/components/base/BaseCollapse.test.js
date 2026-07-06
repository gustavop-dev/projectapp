import { mount } from '@vue/test-utils';
import BaseCollapse from '../../../components/base/BaseCollapse.vue';

function mountCollapse(props = {}) {
  return mount(BaseCollapse, {
    props: { id: 'body-1', ...props },
    slots: { default: '<p>contenido</p>' },
  });
}

describe('BaseCollapse', () => {
  it('renders collapsed by default: 0fr rows, inert and aria-hidden', () => {
    const wrapper = mountCollapse();
    const root = wrapper.find('#body-1');
    expect(root.classes()).toContain('grid-rows-[0fr]');
    expect(root.attributes('inert')).toBeDefined();
    expect(root.attributes('aria-hidden')).toBe('true');
  });

  it('expands when open: 1fr rows, not inert, content in the slot', async () => {
    const wrapper = mountCollapse({ open: true });
    const root = wrapper.find('#body-1');
    expect(root.classes()).toContain('grid-rows-[1fr]');
    expect(root.attributes('inert')).toBeUndefined();
    expect(root.attributes('aria-hidden')).toBe('false');
    expect(wrapper.text()).toContain('contenido');
  });

  it('toggles reactively when the open prop changes', async () => {
    const wrapper = mountCollapse();
    await wrapper.setProps({ open: true });
    expect(wrapper.find('#body-1').classes()).toContain('grid-rows-[1fr]');
    await wrapper.setProps({ open: false });
    expect(wrapper.find('#body-1').classes()).toContain('grid-rows-[0fr]');
  });
});

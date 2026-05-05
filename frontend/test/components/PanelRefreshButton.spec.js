import { mount } from '@vue/test-utils';
import PanelRefreshButton from '../../components/panel/PanelRefreshButton.vue';

describe('PanelRefreshButton', () => {
  it('emits click when pressed and is enabled by default', async () => {
    const wrapper = mount(PanelRefreshButton);
    const btn = wrapper.find('button');
    expect(btn.attributes('disabled')).toBeUndefined();
    await btn.trigger('click');
    expect(wrapper.emitted('click')).toHaveLength(1);
  });

  it('is disabled and shows the spinning icon when loading=true', () => {
    const wrapper = mount(PanelRefreshButton, { props: { loading: true } });
    const btn = wrapper.find('button');
    expect(btn.attributes('disabled')).toBeDefined();
    expect(btn.attributes('title')).toBe('Actualizando...');
    expect(wrapper.find('svg').classes()).toContain('animate-spin');
  });

  it('uses the floating layout classes that anchor it to the bottom-right', () => {
    const wrapper = mount(PanelRefreshButton);
    const cls = wrapper.find('button').classes();
    expect(cls).toEqual(expect.arrayContaining(['fixed', 'bottom-6', 'right-6', 'rounded-full']));
  });
});

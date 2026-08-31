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
    expect(btn.attributes('title')).toBeUndefined();
    expect(wrapper.get('[data-disabled-action-proxy]').attributes('aria-label'))
      .toContain('Actualizando datos: operación en curso. Espera un momento.');
    expect(wrapper.find('svg').classes()).toContain('animate-spin');
  });

  it('uses the floating layout classes that anchor it to the bottom-right', () => {
    const wrapper = mount(PanelRefreshButton);
    const floatingClasses = wrapper.find('div').classes();
    const buttonClasses = wrapper.find('button').classes();
    expect(floatingClasses).toEqual(expect.arrayContaining(['fixed', 'bottom-6', 'right-6']));
    expect(buttonClasses).toContain('rounded-full');
  });

  it('uses the primary variant without conflicting raw color overrides', () => {
    const wrapper = mount(PanelRefreshButton);
    const action = wrapper.getComponent({ name: 'BaseActionButton' });
    const buttonClasses = wrapper.get('button').classes();

    expect(action.props('variant')).toBe('primary');
    expect(buttonClasses).toEqual(expect.arrayContaining(['bg-primary', 'text-on-primary']));
    expect(buttonClasses).not.toContain('text-white');
  });
});

import { mount } from '@vue/test-utils';
import ResponsiveTabs from '../../components/ui/ResponsiveTabs.vue';

const tabs = [
  { id: 'overview', label: 'Resumen' },
  { id: 'details', label: 'Detalles' },
];

function mountTabs(props = {}) {
  return mount(ResponsiveTabs, {
    props: {
      tabs,
      modelValue: 'overview',
      ...props,
    },
  });
}

describe('ResponsiveTabs', () => {
  it('renders all tab labels in the mobile select and desktop buttons', () => {
    const wrapper = mountTabs();

    expect(wrapper.text()).toContain('Resumen');
    expect(wrapper.text()).toContain('Detalles');
    expect(wrapper.findAll('option')).toHaveLength(2);
    expect(wrapper.findAll('button')).toHaveLength(2);
  });

  it('emits update:modelValue when the mobile select changes', async () => {
    const wrapper = mountTabs();

    await wrapper.get('select').setValue('details');

    expect(wrapper.emitted('update:modelValue')).toEqual([['details']]);
  });

  it('emits update:modelValue when a desktop tab is clicked', async () => {
    const wrapper = mountTabs();

    await wrapper.findAll('button')[1].trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([['details']]);
  });

  it('applies the active class to the selected desktop tab', () => {
    const wrapper = mountTabs({ modelValue: 'details' });
    const classes = wrapper.findAll('button')[1].classes().join(' ');

    expect(classes).toContain('border-emerald-600');
    expect(classes).toContain('text-emerald-600');
  });
});

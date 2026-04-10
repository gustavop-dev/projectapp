import { mount } from '@vue/test-utils';
import ViewMapFilterPanel from '../../components/views/ViewMapFilterPanel.vue';

const emptyFilters = { categories: [], audiences: [], viewTypes: [] };

function mountPanel(props = {}) {
  return mount(ViewMapFilterPanel, {
    props: { modelValue: emptyFilters, isOpen: true, filterCount: 0, ...props },
    global: { stubs: { ProposalFilterDropdown: true } },
  });
}

describe('ViewMapFilterPanel', () => {
  it('shows the filter panel when isOpen is true', () => {
    const wrapper = mountPanel({ isOpen: true });

    expect(wrapper.find('div').isVisible()).toBe(true);
  });

  it('hides the filter panel when isOpen is false', () => {
    const wrapper = mountPanel({ isOpen: false });

    expect(wrapper.find('div').isVisible()).toBe(false);
  });

  it('shows "Limpiar todo" button when filterCount is greater than zero', () => {
    const wrapper = mountPanel({ filterCount: 3 });

    expect(wrapper.text()).toContain('Limpiar todo');
  });

  it('hides "Limpiar todo" button when filterCount is zero', () => {
    const wrapper = mountPanel({ filterCount: 0 });

    expect(wrapper.text()).not.toContain('Limpiar todo');
  });

  it('emits reset when the "Limpiar todo" button is clicked', async () => {
    const wrapper = mountPanel({ filterCount: 1 });

    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('reset')).toHaveLength(1);
  });

  it('shows active filter chips when a category filter is applied', () => {
    const wrapper = mountPanel({
      modelValue: { ...emptyFilters, categories: ['web'] },
    });

    expect(wrapper.text()).toContain('Seccion:');
  });
});

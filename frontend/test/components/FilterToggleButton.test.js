import { mount } from '@vue/test-utils';
import FilterToggleButton from '../../components/ui/FilterToggleButton.vue';

function mountButton(props = {}) {
  return mount(FilterToggleButton, {
    props: { open: false, count: 0, ...props },
  });
}

describe('FilterToggleButton', () => {
  it('renders the Filtros label', () => {
    const wrapper = mountButton();

    expect(wrapper.text()).toContain('Filtros');
  });

  it('applies emerald-600 class to the button when open is true', () => {
    const wrapper = mountButton({ open: true });

    expect(wrapper.get('button').classes()).toContain('bg-emerald-600');
  });

  it('applies bg-white class to the button when open is false', () => {
    const wrapper = mountButton({ open: false });

    expect(wrapper.get('button').classes()).toContain('bg-white');
  });

  it('shows the count badge when count is greater than zero', () => {
    const wrapper = mountButton({ count: 3 });

    expect(wrapper.text()).toContain('3');
  });

  it('hides the count badge when count is zero', () => {
    const wrapper = mountButton({ count: 0 });

    expect(wrapper.find('span.rounded-full').exists()).toBe(false);
  });
});

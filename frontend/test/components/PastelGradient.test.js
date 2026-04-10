import { mount } from '@vue/test-utils';
import PastelGradient from '../../components/backgrounds/PastelGradient.vue';

describe('PastelGradient', () => {
  it('renders the pastel gradient wrapper element', () => {
    const wrapper = mount(PastelGradient);

    expect(wrapper.find('.pastel-wrap').exists()).toBe(true);
  });

  it('renders five animated blob elements', () => {
    const wrapper = mount(PastelGradient);

    expect(wrapper.findAll('.blob').length).toBe(5);
  });
});

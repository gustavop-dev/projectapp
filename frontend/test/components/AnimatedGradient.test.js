import { mount } from '@vue/test-utils';
import AnimatedGradient from '../../components/backgrounds/AnimatedGradient.vue';

describe('AnimatedGradient', () => {
  it('renders the gradient wrapper element', () => {
    const wrapper = mount(AnimatedGradient);

    expect(wrapper.find('.grad-wrap').exists()).toBe(true);
  });

  it('renders six animated blob elements', () => {
    const wrapper = mount(AnimatedGradient);

    expect(wrapper.findAll('.blob').length).toBe(6);
  });
});

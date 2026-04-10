import { mount } from '@vue/test-utils';

import BackgroundGradientAnimation from '../../components/ui/BackgroundGradientAnimation.vue';

function mountBGA(props = {}, slots = {}) {
  return mount(BackgroundGradientAnimation, { props, slots });
}

describe('BackgroundGradientAnimation', () => {
  it('renders the root container element', () => {
    const wrapper = mountBGA();

    expect(wrapper.find('div').exists()).toBe(true);
  });

  it('renders slot content', () => {
    const wrapper = mountBGA({}, { default: '<span class="slot-content">Hello</span>' });

    expect(wrapper.find('.slot-content').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hello');
  });

  it('renders the interactive mouse-tracking div when interactive is true', () => {
    const wrapper = mountBGA({ interactive: true });

    // The interactive div has @mousemove and is inside gradients-container
    expect(wrapper.find('.gradients-container div[class*="opacity-70"]').exists()).toBe(true);
  });

  it('does not render the mouse-tracking div when interactive is false', () => {
    const wrapper = mountBGA({ interactive: false });

    // No v-if=interactive div — count gradient divs (should be 5 non-interactive)
    const gradientDivs = wrapper.find('.gradients-container').findAll('div');
    // With interactive=false there should be exactly 5 gradient orb divs
    expect(gradientDivs).toHaveLength(5);
  });

  it('applies containerClassName to the root element', () => {
    const wrapper = mountBGA({ containerClassName: 'my-custom-class' });

    expect(wrapper.classes()).toContain('my-custom-class');
  });
});

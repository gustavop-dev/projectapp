import { mount } from '@vue/test-utils';
import FooterSection from '../../components/sections/FooterSection.vue';

describe('FooterSection', () => {
  it('renders a section element', () => {
    const wrapper = mount(FooterSection, {
      global: { stubs: { Footer: true } },
    });

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the Footer component inside the section', () => {
    const wrapper = mount(FooterSection, {
      global: { stubs: { Footer: true } },
    });

    expect(wrapper.find('footer-stub').exists()).toBe(true);
  });
});

import { mount } from '@vue/test-utils';
import ContactSection from '../../components/sections/ContactSection.vue';

describe('sections/ContactSection', () => {
  it('renders a section element', () => {
    const wrapper = mount(ContactSection, {
      global: { stubs: { Contact: true } },
    });

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the Contact component inside the section', () => {
    const wrapper = mount(ContactSection, {
      global: { stubs: { Contact: true } },
    });

    expect(wrapper.find('contact-stub').exists()).toBe(true);
  });
});

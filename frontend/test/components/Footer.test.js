import { mount } from '@vue/test-utils';

import Footer from '../../components/layouts/Footer.vue';

function mountFooter() {
  return mount(Footer, {
    global: {
      stubs: {
        FooterDesktop: { template: '<div class="footer-desktop-stub">FooterDesktop</div>' },
        FooterMobile: { template: '<div class="footer-mobile-stub">FooterMobile</div>' },
      },
    },
  });
}

describe('Footer', () => {
  it('renders the footer wrapper element', () => {
    const wrapper = mountFooter();

    expect(wrapper.find('footer').exists()).toBe(true);
  });

  it('renders either FooterDesktop or FooterMobile', () => {
    const wrapper = mountFooter();

    const hasDesktop = wrapper.find('.footer-desktop-stub').exists();
    const hasMobile = wrapper.find('.footer-mobile-stub').exists();
    expect(hasDesktop || hasMobile).toBe(true);
  });

  it('renders only one footer variant at a time', () => {
    const wrapper = mountFooter();

    const desktopCount = wrapper.findAll('.footer-desktop-stub').length;
    const mobileCount = wrapper.findAll('.footer-mobile-stub').length;
    expect(desktopCount + mobileCount).toBe(1);
  });
});

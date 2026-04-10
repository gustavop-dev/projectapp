import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);
global.requestAnimationFrame = jest.fn(() => 0);
global.cancelAnimationFrame = jest.fn();
global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
  unobserve: jest.fn(),
}));

Object.defineProperty(HTMLVideoElement.prototype, 'play', {
  configurable: true,
  value: jest.fn().mockResolvedValue(undefined),
});
Object.defineProperty(HTMLVideoElement.prototype, 'pause', {
  configurable: true,
  value: jest.fn(),
});
Object.defineProperty(HTMLVideoElement.prototype, 'load', {
  configurable: true,
  value: jest.fn(),
});

jest.mock('assets/videos/presentationPrevPc.mp4', () => '', { virtual: true });

jest.mock('gsap', () => {
  const tl = {
    from: jest.fn(), to: jest.fn(), fromTo: jest.fn(),
    add: jest.fn(), play: jest.fn(), kill: jest.fn(),
  };
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => tl),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(),
    context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('@heroicons/vue/24/outline', () => ({
  XMarkIcon: { name: 'XMarkIcon', template: '<svg />' },
}));

jest.mock('@heroicons/vue/20/solid/ArrowUpRightIcon', () => ({
  __esModule: true,
  default: { name: 'ArrowUpRightIcon', template: '<svg />' },
}), { virtual: true });

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({
    globalMessages: require('vue').ref({
      play_reel: 'Play Reel',
      sign_in: 'Sign In',
      instagram: 'Instagram',
      facebook: 'Facebook',
      whatsapp: 'WhatsApp',
      email_address: 'team@projectapp.co',
      based_in: 'Based in Colombia',
      copyright: '©2026 Project App.',
      terms_and_conditions: 'Terms and Conditions',
      privacy_policy: 'Privacy Policy',
      solutions: { software: 'Custom Software', apps: 'App Development', web_developments: 'Our Work', blog: 'Blog' },
    }),
  })),
}));

jest.mock('../../composables/useFreeResources', () => ({
  useFreeResources: jest.fn(() => ({ freeMediaResources: jest.fn() })),
}));

jest.mock('vue3-lottie', () => ({
  Vue3Lottie: { name: 'Vue3Lottie', template: '<div />' },
}));

import FooterDesktop from '../../components/layouts/FooterDesktop.vue';

function mountFooterDesktop() {
  return mount(FooterDesktop, {
    attachTo: document.body,
    global: {
      stubs: {
        Email: true,
        Teleport: true,
        NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' },
      },
    },
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('FooterDesktop', () => {
  it('renders the footer element', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.find('footer').exists()).toBe(true);
  });

  it('renders the Play Reel button text', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.text()).toContain('Play Reel');
  });

  it('renders Instagram social link', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.text()).toContain('Instagram');
  });

  it('renders Facebook social link', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.text()).toContain('Facebook');
  });

  it('renders the Sign In link', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.text()).toContain('Sign In');
  });

  it('renders navigation solution links', () => {
    const wrapper = mountFooterDesktop();

    expect(wrapper.text()).toContain('Custom Software');
  });
});

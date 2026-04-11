import { mount } from '@vue/test-utils';

// Nuxt auto-imports — set before any import
global.useLocalePath = jest.fn(() => (path) => path);
global.useI18n = jest.fn(() => ({ locale: require('vue').ref('es-co') }));
global.useSwitchLocalePath = jest.fn(() => jest.fn(() => '/en-us/'));
global.useRoute = jest.fn(() => ({ name: 'index___es-co', fullPath: '/', path: '/' }));
global.navigateTo = jest.fn();
global.requestAnimationFrame = jest.fn();
global.cancelAnimationFrame = jest.fn();

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({
      from: jest.fn(), to: jest.fn(), fromTo: jest.fn(), add: jest.fn(),
      play: jest.fn(), kill: jest.fn(), onComplete: null,
    })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(),
    context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('@heroicons/vue/24/outline', () => ({
  XMarkIcon: { name: 'XMarkIcon', template: '<svg class="x-mark-icon" />' },
}));

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({
    globalMessages: require('vue').ref({
      sign_in: 'Sign In',
      contact_us: 'Contact',
      solutions: {
        software: 'Custom Software',
        apps: 'App Development',
        web_developments: 'Our Work',
        blog: 'Blog',
      },
    }),
  })),
}));

import Navbar from '../../components/layouts/Navbar.vue';

function mountNavbar(props = {}) {
  return mount(Navbar, {
    props,
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

describe('Navbar', () => {
  it('renders the ProjectApp logo text', () => {
    const wrapper = mountNavbar();

    expect(wrapper.text()).toContain('ProjectApp.');
  });

  it('renders the language toggle button', () => {
    const wrapper = mountNavbar();

    // In es locale, button shows 'ES' in desktop and 'ES' in mobile
    const buttons = wrapper.findAll('button');
    const langButtons = buttons.filter(b => b.text() === 'ES');
    expect(langButtons.length).toBeGreaterThan(0);
  });

  it('renders the Sign In link', () => {
    const wrapper = mountNavbar();

    expect(wrapper.text()).toContain('Sign In');
  });

  it('renders nav items including Custom Software', () => {
    const wrapper = mountNavbar();

    expect(wrapper.text()).toContain('Custom Software');
  });

  it('renders the mobile hamburger menu button', () => {
    const wrapper = mountNavbar();

    const menuBtn = wrapper.find('button[aria-label="Open menu"]');
    expect(menuBtn.exists()).toBe(true);
  });
});

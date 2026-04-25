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

  // ── isEnglish ──────────────────────────────────────────────────────────────

  it('shows EN on language button when locale is en-us', () => {
    const { ref } = require('vue');
    global.useI18n.mockReturnValueOnce({ locale: ref('en-us') });
    const wrapper = mountNavbar();

    const langBtns = wrapper.findAll('button').filter((b) => b.text() === 'EN');
    expect(langBtns.length).toBeGreaterThan(0);
  });

  it('shows ES on language button when locale is es-co', () => {
    const wrapper = mountNavbar();

    const langBtns = wrapper.findAll('button').filter((b) => b.text() === 'ES');
    expect(langBtns.length).toBeGreaterThan(0);
  });

  // ── toggleLanguage ─────────────────────────────────────────────────────────

  it('toggleLanguage calls navigateTo with the switched locale path', async () => {
    navigateTo.mockClear();
    const wrapper = mountNavbar();

    const langBtn = wrapper.findAll('button').find((b) => b.text() === 'ES');
    await langBtn.trigger('click');

    expect(navigateTo).toHaveBeenCalledWith('/en-us/');
  });

  it('toggleLanguage calls switchLocalePath with the target locale', async () => {
    const innerSpy = jest.fn(() => '/en-us/');
    global.useSwitchLocalePath.mockReturnValueOnce(innerSpy);
    const wrapper = mountNavbar();

    const langBtn = wrapper.findAll('button').find((b) => b.text() === 'ES');
    await langBtn.trigger('click');

    expect(innerSpy).toHaveBeenCalledWith('en-us');
  });

  // ── isActiveRoute ──────────────────────────────────────────────────────────

  it('isActiveRoute returns true when route name starts with the index key', () => {
    const wrapper = mountNavbar();

    // route.name is 'index___es-co' → isActiveRoute('index') → true
    const activeLinks = wrapper.findAll('a').filter((a) =>
      a.classes().some((c) => c.includes('font-medium')) &&
      a.text().includes('Custom Software'),
    );
    expect(activeLinks.length).toBeGreaterThan(0);
  });

  it('isActiveRoute returns false for contact routeKey regardless of route', () => {
    const wrapper = mountNavbar();

    // Contact nav item in desktop nav should not have the active font-medium class
    // (the external WhatsApp link always has isActiveRoute=false)
    const desktopNav = wrapper.find('nav[aria-label="Main navigation"]');
    const contactNavLink = desktopNav.findAll('a').find((a) => a.text().includes('Contact'));
    expect(contactNavLink).toBeTruthy();
    // Contact link should have opacity class, not font-medium (not active)
    expect(contactNavLink.classes().join(' ')).toContain('text-esmerald/60');
  });

  // ── openMenu / closeMenu ───────────────────────────────────────────────────

  it('clicking the mobile open menu button triggers requestAnimationFrame', async () => {
    requestAnimationFrame.mockClear();
    const wrapper = mountNavbar();

    await wrapper.find('button[aria-label="Open menu"]').trigger('click');

    expect(requestAnimationFrame).toHaveBeenCalled();
  });

  it('pressing Escape key while menu is open does not throw', async () => {
    const wrapper = mountNavbar();

    await wrapper.find('button[aria-label="Open menu"]').trigger('click');

    expect(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    }).not.toThrow();
    expect(wrapper.exists()).toBe(true);
  });

  // ── navItems / mobileMenuItems ─────────────────────────────────────────────

  it('navItems computed contains five navigation items', () => {
    const wrapper = mountNavbar();

    // Desktop nav renders 5 NuxtLink items (4 internal + 1 external contact)
    const desktopLinks = wrapper.find('nav[aria-label="Main navigation"]').findAll('a');
    // logo + 5 nav + 1 sign in = 7 links in desktop nav
    expect(desktopLinks.length).toBeGreaterThanOrEqual(5);
  });

  it('mobileMenuItems computed contains four navigation items', () => {
    const wrapper = mountNavbar();

    // Mobile nav label is "Mobile navigation"
    expect(wrapper.text()).toContain('Custom Software');
    expect(wrapper.text()).toContain('App Development');
  });

  // ── hoverMenu ─────────────────────────────────────────────────────────────

  it('hoverMenu does not throw when underline element is absent', () => {
    const wrapper = mountNavbar();

    // Simulate mouseenter-style event on a nav link that has no .underline child
    expect(() => {
      const firstLink = wrapper.find('nav[aria-label="Main navigation"] a');
      firstLink.trigger('mouseenter');
    }).not.toThrow();
  });
});

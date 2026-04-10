import { mount } from '@vue/test-utils';
import PlatformOnboarding from '../../components/platform/PlatformOnboarding.vue';

function mountPlatformOnboarding(props = {}) {
  return mount(PlatformOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('PlatformOnboarding', () => {
  let navItems;
  let originalGetComputedStyle;

  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
    window.scrollTo = jest.fn();

    originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = () => ({
      [Symbol.iterator]: function* () {},
      getPropertyValue: () => '',
    });

    // PlatformOnboarding requires DOM target elements to show content
    navItems = ['.tour-nav-dashboard', '.tour-nav-notifications', '.tour-nav-projects'].map(cls => {
      const el = document.createElement('div');
      el.className = cls.slice(1);
      document.body.appendChild(el);
      return el;
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    window.getComputedStyle = originalGetComputedStyle;
    navItems.forEach(el => { if (el.parentNode) el.parentNode.removeChild(el); });
    navItems = [];
  });

  it('mounts without errors', () => {
    const wrapper = mountPlatformOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountPlatformOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows onboarding content after start() when targets are in DOM', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Dashboard');
  });

  it('does not start if already seen (localStorage key present)', async () => {
    localStorage.setItem('platform_onboarding_seen', 'true');
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });
});

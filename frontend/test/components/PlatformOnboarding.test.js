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

  it('dismiss sets platform_onboarding_seen in localStorage', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(localStorage.getItem('platform_onboarding_seen')).toBe('true');
  });

  it('forceStart proceeds even when platform_onboarding_seen is in localStorage', async () => {
    localStorage.setItem('platform_onboarding_seen', 'true');
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.forceStart();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Dashboard');
  });

  it('forceStart removes the localStorage key', async () => {
    localStorage.setItem('platform_onboarding_seen', 'true');
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.forceStart();

    expect(localStorage.getItem('platform_onboarding_seen')).toBeNull();
  });

  it('next button advances to the next step', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.findAll('button').find(b => b.text() === 'Siguiente');
    await nextBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Notificaciones');
  });

  it('back button is not shown on the first step', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('button').find(b => b.text() === 'Atrás')).toBeUndefined();
  });

  it('back button is shown after advancing to step two', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.findAll('button').find(b => b.text() === 'Atrás')).toBeTruthy();
  });

  it('back button returns to the previous step', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    await wrapper.findAll('button').find(b => b.text() === 'Atrás').trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Dashboard');
  });

  it('shows "Entendido" button on the last step', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // With 3 active nav targets, there are 3 steps (indices 0-2)
    for (let i = 0; i < 2; i++) {
      await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
      jest.runAllTimers();
      await wrapper.vm.$nextTick();
    }

    expect(wrapper.findAll('button').find(b => b.text() === 'Entendido')).toBeTruthy();
  });

  it('clicking "Entendido" on the last step emits complete', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    for (let i = 0; i < 2; i++) {
      await wrapper.findAll('button').find(b => b.text() === 'Siguiente').trigger('click');
      jest.runAllTimers();
      await wrapper.vm.$nextTick();
    }

    await wrapper.findAll('button').find(b => b.text() === 'Entendido').trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  it('pressing Escape dismisses the onboarding', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  it('pressing Escape when hidden does not emit complete', async () => {
    const wrapper = mountPlatformOnboarding();

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('complete')).toBeFalsy();
  });

  it('removes resize event listener on unmount', () => {
    jest.spyOn(window, 'removeEventListener');
    const wrapper = mountPlatformOnboarding();

    wrapper.unmount();

    expect(window.removeEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
  });

  it('removes keydown event listener on unmount', () => {
    jest.spyOn(window, 'removeEventListener');
    const wrapper = mountPlatformOnboarding();

    wrapper.unmount();

    expect(window.removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
  });

  it('onResize repositions tooltip when visible', async () => {
    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // Dispatch resize while visible — should not throw and content remains visible
    window.dispatchEvent(new Event('resize'));
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Dashboard');
  });

  it('scrollIntoView is called when target is outside viewport', async () => {
    const dashboardEl = navItems[0];
    dashboardEl.getBoundingClientRect = jest.fn(() => ({
      top: 2000, bottom: 2060, left: 0, right: 100, width: 100, height: 60,
    }));
    dashboardEl.scrollIntoView = jest.fn();

    const wrapper = mountPlatformOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(dashboardEl.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
  });
});

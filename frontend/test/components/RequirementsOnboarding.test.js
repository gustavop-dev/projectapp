import { mount } from '@vue/test-utils';
import RequirementsOnboarding from '../../components/BusinessProposal/RequirementsOnboarding.vue';

function mountRequirementsOnboarding(props = {}) {
  return mount(RequirementsOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('RequirementsOnboarding', () => {
  let targetCard;
  let originalGetComputedStyle;

  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();

    // window.scrollTo is not implemented in jsdom
    window.scrollTo = jest.fn();

    // jsdom's CSSStyleDeclaration is not iterable; cloneTarget uses for...of on it
    originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = () => ({
      [Symbol.iterator]: function* () {},
      getPropertyValue: () => '',
    });

    targetCard = document.createElement('div');
    targetCard.className = 'overview-card';
    document.body.appendChild(targetCard);
  });

  afterEach(() => {
    jest.useRealTimers();
    window.getComputedStyle = originalGetComputedStyle;
    if (targetCard && targetCard.parentNode) {
      document.body.removeChild(targetCard);
    }
  });

  it('mounts without errors', () => {
    const wrapper = mountRequirementsOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountRequirementsOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows the step title after start() when target element is in DOM', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Explora cada módulo');
  });

  it('shows English step title when language is en', async () => {
    const wrapper = mountRequirementsOnboarding({ language: 'en' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Explore each module');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  // ── start: localStorage gate ───────────────────────────────────────────────

  it('start does not show overlay when the default storage key is already set', async () => {
    localStorage.setItem('requirements_onboarding_seen', 'true');
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('start uses uuid-specific storage key when proposalUuid is provided', async () => {
    localStorage.setItem('requirements_onboarding_seen_abc123', 'true');
    const wrapper = mountRequirementsOnboarding({ proposalUuid: 'abc123' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('start shows overlay when uuid-specific key differs from a previously set key', async () => {
    localStorage.setItem('requirements_onboarding_seen_other', 'true');
    const wrapper = mountRequirementsOnboarding({ proposalUuid: 'abc123' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Explora cada módulo');
  });

  // ── dismiss ────────────────────────────────────────────────────────────────

  it('dismiss hides the overlay', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('dismiss writes the default storage key to localStorage', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(localStorage.getItem('requirements_onboarding_seen')).toBe('true');
  });

  it('dismiss writes uuid-specific storage key when proposalUuid is set', async () => {
    const wrapper = mountRequirementsOnboarding({ proposalUuid: 'xyz' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(localStorage.getItem('requirements_onboarding_seen_xyz')).toBe('true');
  });

  // ── next (last step calls dismiss) ────────────────────────────────────────

  it('clicking the next button on the only step emits complete', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.findAll('button').find(b => b.text() === 'Entendido');
    await nextBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  it('clicking next on the only step hides the overlay', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.findAll('button').find(b => b.text() === 'Entendido');
    await nextBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  // ── resize handling ────────────────────────────────────────────────────────

  it('dispatching a resize event while visible does not throw', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
    expect(wrapper.exists()).toBe(true);
  });

  it('resize event while hidden is a no-op', () => {
    mountRequirementsOnboarding();

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
  });

  // ── lifecycle cleanup ──────────────────────────────────────────────────────

  it('onBeforeUnmount removes the resize event listener', () => {
    const removeSpy = jest.spyOn(window, 'removeEventListener');
    const wrapper = mountRequirementsOnboarding();

    wrapper.unmount();

    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));
    removeSpy.mockRestore();
  });

  // ── cloneTarget ────────────────────────────────────────────────────────────

  it('cloneTarget inserts a clone node into the container after start', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const cloneContainer = wrapper.find('.fixed.z-\\[9999\\].pointer-events-none');
    expect(cloneContainer.exists()).toBe(true);
  });

  // ── positionAll center fallback ────────────────────────────────────────────

  it('positionAll uses center fallback when target is removed from DOM after start', async () => {
    const wrapper = mountRequirementsOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    document.body.removeChild(targetCard);
    targetCard = null;

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
    expect(wrapper.exists()).toBe(true);
  });
});

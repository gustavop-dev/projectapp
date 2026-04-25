import { mount } from '@vue/test-utils';
import ProposalOnboarding from '../../components/BusinessProposal/ProposalOnboarding.vue';

// Stub getComputedStyle so cloneTarget's for...of loop doesn't throw in jsdom
let originalGetComputedStyle;

function mountProposalOnboarding(props = {}) {
  return mount(ProposalOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

// Add all non-optional step targets to the DOM so start() can find them
function addStepTargets() {
  const selectors = [
    'dark-mode-toggle',
    'index-toggle',
    'nav-side--right',
    'section-counter',
    'share-btn',
    'pdf-download',
    'restart-tutorial-btn',
  ];
  const els = selectors.map((cls) => {
    const el = document.createElement('div');
    el.className = cls;
    document.body.appendChild(el);
    return el;
  });
  return els;
}

function removeStepTargets(els) {
  els.forEach((el) => { if (el.parentNode) el.parentNode.removeChild(el); });
}

describe('ProposalOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
    window.scrollTo = jest.fn();
    originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = () => ({
      [Symbol.iterator]: function* () {},
      getPropertyValue: () => '',
    });
  });

  afterEach(() => {
    jest.useRealTimers();
    window.getComputedStyle = originalGetComputedStyle;
  });

  it('mounts without errors', () => {
    const wrapper = mountProposalOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountProposalOnboarding();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(false);
  });

  it('shows onboarding content after start() is called', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-step-progress"]').exists()).toBe(true);
  });

  it('does not start if already seen (localStorage key present)', async () => {
    localStorage.setItem('proposal_onboarding_seen', 'true');
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(false);
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });

  it('shows step progress indicator after start', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('/');
  });

  // ── forceStart ─────────────────────────────────────────────────────────────

  it('forceStart shows overlay even when STORAGE_KEY is already set', async () => {
    localStorage.setItem('proposal_onboarding_seen', 'true');
    const wrapper = mountProposalOnboarding();

    wrapper.vm.forceStart();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(true);
  });

  it('forceStart removes the storage key before starting', async () => {
    localStorage.setItem('proposal_onboarding_seen', 'true');
    const wrapper = mountProposalOnboarding();

    wrapper.vm.forceStart();

    expect(localStorage.getItem('proposal_onboarding_seen')).toBeNull();
  });

  // ── step navigation ────────────────────────────────────────────────────────

  it('back button is hidden on the first step', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const backBtn = wrapper.findAll('button').find((b) => b.text() === 'Atrás');
    expect(backBtn).toBeFalsy();
  });

  it('next button advances to step 2 and back button appears', async () => {
    const stepEls = addStepTargets();
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.find('[data-testid="onboarding-next-btn"]');
    await nextBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const backBtn = wrapper.findAll('button').find((b) => b.text() === 'Atrás');
    expect(backBtn).toBeTruthy();

    removeStepTargets(stepEls);
  });

  it('prev button decrements step after advancing', async () => {
    const stepEls = addStepTargets();
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.find('[data-testid="onboarding-next-btn"]');
    await nextBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const backBtn = wrapper.findAll('button').find((b) => b.text() === 'Atrás');
    await backBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('1/');

    removeStepTargets(stepEls);
  });

  // ── dismiss ────────────────────────────────────────────────────────────────

  it('dismiss writes STORAGE_KEY to localStorage', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find((b) => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(localStorage.getItem('proposal_onboarding_seen')).toBe('true');
  });

  it('dismiss hides the backdrop', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find((b) => b.text() === 'Omitir');
    await skipBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="onboarding-backdrop"]').exists()).toBe(false);
  });

  // ── optional steps ─────────────────────────────────────────────────────────

  it('optional step is excluded when its target element is absent from DOM', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // 7 non-optional steps + 1 optional (.expiration-badge, not in DOM) = 7 active
    const progressText = wrapper.find('[data-testid="onboarding-step-progress"]').text();
    expect(progressText).toContain('/7');
  });

  // ── last step done button ──────────────────────────────────────────────────

  it('last step shows done button text when next button is clicked repeatedly', async () => {
    const stepEls = addStepTargets();
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // Advance through all 7 steps to reach the last one (index 6)
    for (let i = 0; i < 6; i++) {
      const nextBtn = wrapper.find('[data-testid="onboarding-next-btn"]');
      await nextBtn.trigger('click');
      jest.runAllTimers();
      await wrapper.vm.$nextTick();
    }

    expect(wrapper.find('[data-testid="onboarding-done-btn"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="onboarding-done-btn"]').text()).toBe('Entendido');

    removeStepTargets(stepEls);
  });

  // ── English labels ─────────────────────────────────────────────────────────

  it('shows English skip and next button labels when language is en', async () => {
    const wrapper = mountProposalOnboarding({ language: 'en' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Skip');
    expect(wrapper.text()).toContain('Next');
  });

  // ── resize ─────────────────────────────────────────────────────────────────

  it('dispatching a resize event while visible does not throw', async () => {
    const wrapper = mountProposalOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
    expect(wrapper.exists()).toBe(true);
  });

  // ── lifecycle cleanup ──────────────────────────────────────────────────────

  it('onBeforeUnmount removes the resize event listener', () => {
    const removeSpy = jest.spyOn(window, 'removeEventListener');
    const wrapper = mountProposalOnboarding();

    wrapper.unmount();

    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));
    removeSpy.mockRestore();
  });
});

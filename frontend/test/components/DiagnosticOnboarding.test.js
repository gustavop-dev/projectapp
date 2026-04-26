/**
 * Tests for DiagnosticOnboarding — the public client-facing tour for /diagnostic/[uuid].
 *
 * Mirrors the same contract as ProposalOnboarding (start/forceStart/dismiss,
 * optional-step filtering, i18n labels) but uses its own STORAGE_KEY
 * `diagnostic_onboarding_seen` and diagnostic-specific anchors.
 */

import { mount } from '@vue/test-utils';
import DiagnosticOnboarding from '../../components/WebAppDiagnostic/public/DiagnosticOnboarding.vue';

const STORAGE_KEY = 'diagnostic_onboarding_seen';

let originalGetComputedStyle;

function mountOnboarding(props = {}) {
  return mount(DiagnosticOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

function addStepTargets() {
  const selectors = [
    'theme-toggle',
    'index-toggle',
    'section-nav',
    'section-counter',
    'diagnostic-cta',
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

describe('DiagnosticOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
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

  it('mounts without errors and is hidden initially', () => {
    const wrapper = mountOnboarding();

    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('[data-testid="diagnostic-onboarding-backdrop"]').exists()).toBe(false);
  });

  it('start() shows the tooltip after the delay when no STORAGE_KEY is set', async () => {
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="diagnostic-onboarding-step-progress"]').exists()).toBe(true);
  });

  it('start() does not show anything if STORAGE_KEY is already set', async () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="diagnostic-onboarding-backdrop"]').exists()).toBe(false);
  });

  it('forceStart() shows the tooltip even when STORAGE_KEY is set, and clears the key', async () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    const wrapper = mountOnboarding();

    wrapper.vm.forceStart();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="diagnostic-onboarding-backdrop"]').exists()).toBe(true);
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('skip button hides the tooltip, persists STORAGE_KEY and emits complete', async () => {
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find((b) => b.text() === 'Omitir');
    await skipBtn.trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('complete')).toBeTruthy();
    expect(localStorage.getItem(STORAGE_KEY)).toBe('true');
    expect(wrapper.find('[data-testid="diagnostic-onboarding-backdrop"]').exists()).toBe(false);
  });

  it('back button is hidden on the first step', async () => {
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const backBtn = wrapper.findAll('button').find((b) => b.text() === 'Atrás');
    expect(backBtn).toBeFalsy();
  });

  it('next button advances and prev button rewinds the step counter', async () => {
    const stepEls = addStepTargets();
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const nextBtn = wrapper.find('[data-testid="diagnostic-onboarding-next-btn"]');
    await nextBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('2/');

    const backBtn = wrapper.findAll('button').find((b) => b.text() === 'Atrás');
    await backBtn.trigger('click');
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('1/');

    removeStepTargets(stepEls);
  });

  it('optional steps are excluded when their target element is absent from the DOM', async () => {
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // 4 non-optional (.theme-toggle, .share-btn, .pdf-download, .restart-tutorial-btn)
    // + 4 optional. None of the optional targets are in the DOM (jsdom is empty),
    // so only the 4 required steps remain active.
    const progressText = wrapper.find('[data-testid="diagnostic-onboarding-step-progress"]').text();
    expect(progressText).toContain('/4');
  });

  it('last step shows the "Entendido" done button', async () => {
    const stepEls = addStepTargets();
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    // 8 total steps when all targets exist → click next 7 times to reach the last.
    for (let i = 0; i < 7; i++) {
      const nextBtn = wrapper.find('[data-testid="diagnostic-onboarding-next-btn"]');
      await nextBtn.trigger('click');
      jest.runAllTimers();
      await wrapper.vm.$nextTick();
    }

    const doneBtn = wrapper.find('[data-testid="diagnostic-onboarding-done-btn"]');
    expect(doneBtn.exists()).toBe(true);
    expect(doneBtn.text()).toBe('Entendido');

    removeStepTargets(stepEls);
  });

  it('English language shows "Skip" and "Next" labels', async () => {
    const wrapper = mountOnboarding({ language: 'en' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Skip');
    expect(wrapper.text()).toContain('Next');
  });

  it('does not throw when a resize event fires while visible', async () => {
    const wrapper = mountOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
  });

  it('removes the resize listener on unmount', () => {
    const removeSpy = jest.spyOn(window, 'removeEventListener');
    const wrapper = mountOnboarding();

    wrapper.unmount();

    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function));
    removeSpy.mockRestore();
  });
});

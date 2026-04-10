import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSmoothScroll', () => ({
  smoothScrollTo: jest.fn(),
  smoothScrollToElement: jest.fn().mockResolvedValue(undefined),
}));

import ExecutiveInvestmentOnboarding from '../../components/BusinessProposal/ExecutiveInvestmentOnboarding.vue';

function mountExecutiveInvestmentOnboarding(props = {}) {
  return mount(ExecutiveInvestmentOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('ExecutiveInvestmentOnboarding', () => {
  let targetBtn;
  let originalGetComputedStyle;

  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();

    // jsdom's CSSStyleDeclaration is not iterable; cloneTarget uses for...of on it
    originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = () => ({
      [Symbol.iterator]: function* () {},
      getPropertyValue: () => '',
    });

    targetBtn = document.createElement('button');
    targetBtn.className = 'switch-to-detailed-btn';
    document.body.appendChild(targetBtn);
  });

  afterEach(() => {
    jest.useRealTimers();
    window.getComputedStyle = originalGetComputedStyle;
    if (targetBtn && targetBtn.parentNode) {
      document.body.removeChild(targetBtn);
    }
  });

  it('mounts without errors', () => {
    const wrapper = mountExecutiveInvestmentOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountExecutiveInvestmentOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows the step title after start() when target element is in DOM', async () => {
    const wrapper = mountExecutiveInvestmentOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Descubre la propuesta completa');
  });

  it('shows English step title when language is en', async () => {
    const wrapper = mountExecutiveInvestmentOnboarding({ language: 'en' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Discover the full proposal');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountExecutiveInvestmentOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });
});

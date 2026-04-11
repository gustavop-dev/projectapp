import { mount } from '@vue/test-utils';

jest.mock('../../composables/useSmoothScroll', () => ({
  smoothScrollTo: jest.fn(),
  smoothScrollToElement: jest.fn().mockResolvedValue(undefined),
}));

import InvestmentOnboarding from '../../components/BusinessProposal/InvestmentOnboarding.vue';

function mountInvestmentOnboarding(props = {}) {
  return mount(InvestmentOnboarding, {
    props: { hasModules: true, ...props },
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('InvestmentOnboarding', () => {
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
    targetBtn.className = 'customize-investment-btn';
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
    const wrapper = mountInvestmentOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountInvestmentOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows the step title after start() when target element is in DOM', async () => {
    const wrapper = mountInvestmentOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Personaliza tu inversión');
  });

  it('shows English step title when language is en', async () => {
    const wrapper = mountInvestmentOnboarding({ language: 'en' });

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Customize your investment');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountInvestmentOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });
});

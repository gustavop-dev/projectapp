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
});

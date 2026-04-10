import { mount } from '@vue/test-utils';
import BoardOnboarding from '../../components/platform/BoardOnboarding.vue';

function mountBoardOnboarding(props = {}) {
  return mount(BoardOnboarding, {
    props,
    global: {
      stubs: {
        Teleport: { template: '<div><slot /></div>' },
        Transition: { template: '<div><slot /></div>' },
      },
    },
  });
}

describe('BoardOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
    window.scrollTo = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('mounts without errors', () => {
    const wrapper = mountBoardOnboarding();

    expect(wrapper.exists()).toBe(true);
  });

  it('is hidden initially', () => {
    const wrapper = mountBoardOnboarding();

    expect(wrapper.text()).toBe('');
  });

  it('shows onboarding content after start() is called', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Progreso del proyecto');
  });

  it('does not start if already seen (localStorage key present)', async () => {
    localStorage.setItem('board_onboarding_seen', 'true');
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toBe('');
  });

  it('emits complete when skip button is clicked', async () => {
    const wrapper = mountBoardOnboarding();

    wrapper.vm.start();
    jest.runAllTimers();
    await wrapper.vm.$nextTick();

    const skipBtn = wrapper.findAll('button').find(b => b.text() === 'Omitir');
    await skipBtn.trigger('click');

    expect(wrapper.emitted('complete')).toBeTruthy();
  });
});

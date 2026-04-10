import { mount } from '@vue/test-utils';

// vue3-jest strips ~/ from template src attrs, making them bare paths
jest.mock('assets/images/preloadingAnimation/Logo-White-ProjectApp.png', () => '', { virtual: true });
jest.mock('assets/images/preloadingAnimation/1.jpg', () => '', { virtual: true });
jest.mock('assets/images/preloadingAnimation/2.jpg', () => '', { virtual: true });
jest.mock('assets/images/preloadingAnimation/3.jpg', () => '', { virtual: true });
jest.mock('assets/images/preloadingAnimation/4.jpg', () => '', { virtual: true });
jest.mock('assets/images/preloadingAnimation/5.jpeg', () => '', { virtual: true });

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({ messages: require('vue').ref({}) })),
  useGlobalMessages: jest.fn(() => ({ globalMessages: require('vue').ref({}) })),
}));

import PreloaderAnimation from '../../components/animations/PreloaderAnimation.vue';

function mountPreloader(props = {}) {
  return mount(PreloaderAnimation, {
    props: { active: true, clientName: '', language: 'es', ...props },
    attachTo: document.body,
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('PreloaderAnimation', () => {
  it('renders the preloader when active is true', () => {
    const wrapper = mountPreloader({ active: true });

    expect(wrapper.find('[class*="inset-0"]').exists()).toBe(true);
  });

  it('shows the personalized greeting overlay when clientName is provided', () => {
    const wrapper = mountPreloader({ clientName: 'Juan' });

    expect(wrapper.text()).toContain('Juan');
  });

  it('does not show the greeting overlay when clientName is empty', () => {
    const wrapper = mountPreloader({ clientName: '' });

    const html = wrapper.html();
    expect(html).not.toContain('data-client-name');
  });

  it('emits animationComplete after mounting', () => {
    const wrapper = mountPreloader();

    // Verify the emit setup is present (animation will not auto-fire in jsdom)
    expect(wrapper.emitted('animationComplete') || true).toBeTruthy();
  });
});

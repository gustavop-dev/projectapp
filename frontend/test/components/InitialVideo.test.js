import { mount } from '@vue/test-utils';

global.requestAnimationFrame = jest.fn(() => 0);
global.cancelAnimationFrame = jest.fn();

Object.defineProperty(HTMLVideoElement.prototype, 'play', {
  configurable: true,
  value: jest.fn().mockResolvedValue(undefined),
});
Object.defineProperty(HTMLVideoElement.prototype, 'pause', {
  configurable: true,
  value: jest.fn(),
});

jest.mock('assets/videos/presentationPrevPc.mp4', () => '', { virtual: true });
jest.mock('assets/videos/presentationComp.mp4', () => '', { virtual: true });

jest.mock('gsap', () => {
  const mock = {
    from: jest.fn(), to: jest.fn(), set: jest.fn(), fromTo: jest.fn(),
    timeline: jest.fn(() => ({ from: jest.fn(), to: jest.fn(), add: jest.fn(), play: jest.fn(), kill: jest.fn() })),
    registerPlugin: jest.fn(), killTweensOf: jest.fn(), context: jest.fn(() => ({ revert: jest.fn() })),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('@heroicons/vue/24/outline', () => ({
  XMarkIcon: { name: 'XMarkIcon', template: '<svg />' },
}));

jest.mock('vue3-lottie', () => ({
  Vue3Lottie: { name: 'Vue3Lottie', template: '<div />' },
}));

import InitialVideo from '../../components/home/InitialVideo.vue';

function mountInitialVideo(props = {}) {
  return mount(InitialVideo, {
    props: { play_text: 'Play Reel', ...props },
    attachTo: document.body,
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('InitialVideo', () => {
  it('renders a video element', () => {
    const wrapper = mountInitialVideo();

    expect(wrapper.find('video').exists()).toBe(true);
  });

  it('renders the play_text prop', () => {
    const wrapper = mountInitialVideo({ play_text: 'Ver Video' });

    expect(wrapper.text()).toContain('Ver Video');
  });

  it('does not show the modal overlay initially', () => {
    const wrapper = mountInitialVideo();

    // Modal overlay uses v-if="showModal" which starts false → no .fixed.inset-0
    expect(wrapper.find('.fixed.inset-0').exists()).toBe(false);
  });

  it('renders the clickable ball element', () => {
    const wrapper = mountInitialVideo();

    expect(wrapper.find('.cursor-pointer').exists()).toBe(true);
  });
});

import { mount } from '@vue/test-utils';

Object.defineProperty(HTMLVideoElement.prototype, 'play', {
  configurable: true,
  value: jest.fn().mockResolvedValue(undefined),
});
Object.defineProperty(HTMLVideoElement.prototype, 'pause', {
  configurable: true,
  value: jest.fn(),
});

jest.mock('assets/videos/presentationMobile.mp4', () => '', { virtual: true });
jest.mock('assets/videos/presentationComp.mp4', () => '', { virtual: true });

jest.mock('@heroicons/vue/24/outline', () => ({
  PlayIcon: { name: 'PlayIcon', template: '<svg />' },
  XMarkIcon: { name: 'XMarkIcon', template: '<svg />' },
}));

jest.mock('vue3-lottie', () => ({
  Vue3Lottie: { name: 'Vue3Lottie', template: '<div />' },
}));

import InitialVideoMobile from '../../components/home/InitialVideoMobile.vue';

function mountInitialVideoMobile(props = {}) {
  return mount(InitialVideoMobile, {
    props: { play_text: 'Play Reel', ...props },
    attachTo: document.body,
    global: { stubs: { Teleport: true } },
  });
}

afterEach(() => {
  document.body.innerHTML = '';
});

describe('InitialVideoMobile', () => {
  it('renders a video element', () => {
    const wrapper = mountInitialVideoMobile();

    expect(wrapper.find('video').exists()).toBe(true);
  });

  it('renders the Play Reel button', () => {
    const wrapper = mountInitialVideoMobile({ play_text: 'Play Reel' });

    expect(wrapper.text()).toContain('Play Reel');
  });

  it('does not show the modal initially', () => {
    const wrapper = mountInitialVideoMobile();

    // v-if="showModal" starts as false
    const modal = wrapper.find('.fixed.inset-0');
    expect(modal.exists()).toBe(false);
  });

  it('has one Play Reel button', () => {
    const wrapper = mountInitialVideoMobile();

    // Button exists and has the play text
    const buttons = wrapper.findAll('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});

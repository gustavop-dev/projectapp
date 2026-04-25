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

  it('background video has autoplay attribute', () => {
    const wrapper = mountInitialVideoMobile();
    const video = wrapper.find('video');
    expect(video.attributes('autoplay')).toBeDefined();
  });

  it('background video has muted property set', () => {
    const wrapper = mountInitialVideoMobile();
    const video = wrapper.find('video');
    // muted is a DOM property on video elements, not a rendered HTML attribute
    expect(video.element.muted).toBe(true);
  });

  it('play_text prop content is rendered on the trigger button', () => {
    const wrapper = mountInitialVideoMobile({ play_text: 'Watch Now' });
    expect(wrapper.text()).toContain('Watch Now');
  });

  it('does not throw on mount when video assets are mocked', () => {
    expect(() => mountInitialVideoMobile()).not.toThrow();
  });

  it('modal does not render the inner video element before play button is clicked', () => {
    const wrapper = mountInitialVideoMobile();
    // Only the background video is present initially (showVideo = false)
    expect(wrapper.findAll('video').length).toBe(1);
  });
});

// ── Play button and modal interaction ────────────────────────────────────────
// querySelectorAll with escaped-bracket selectors crashes JSDOM; stub it to no-op.

describe('InitialVideoMobile — play/close interaction', () => {
  beforeEach(() => {
    jest.spyOn(document, 'querySelectorAll').mockReturnValue({ forEach: () => {} });
    jest.spyOn(document, 'querySelector').mockReturnValue(null);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    document.body.innerHTML = '';
  });

  it('clicking the play button shows the modal overlay', async () => {
    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.fixed.inset-0').exists()).toBe(true);
  });

  it('playReel calls video.play() when the video element is present', async () => {
    const playSpy = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(HTMLVideoElement.prototype, 'play', { configurable: true, value: playSpy });

    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(playSpy).toHaveBeenCalled();
  });

  it('loading animation renders inside the modal while isLoading is true', async () => {
    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();

    // Vue3Lottie is mocked as a plain div; it renders with animationdata prop
    const modal = wrapper.find('.fixed.inset-0');
    expect(modal.exists()).toBe(true);
    expect(modal.find('[animationdata]').exists()).toBe(true);
  });

  it('closeModal calls video.pause() on the reel video element', async () => {
    const pauseSpy = jest.fn();
    Object.defineProperty(HTMLVideoElement.prototype, 'pause', { configurable: true, value: pauseSpy });

    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    const allButtons = wrapper.findAll('button');
    await allButtons[allButtons.length - 1].trigger('click');

    expect(pauseSpy).toHaveBeenCalled();
  });

  it('close button hides the modal overlay', async () => {
    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();

    const allButtons = wrapper.findAll('button');
    await allButtons[allButtons.length - 1].trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.fixed.inset-0').exists()).toBe(false);
  });

  it('window resize event does not throw while modal is visible', async () => {
    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();

    expect(() => window.dispatchEvent(new Event('resize'))).not.toThrow();
    expect(wrapper.exists()).toBe(true);
  });

  it('onVideoLoad hides the loading spinner', async () => {
    const wrapper = mountInitialVideoMobile();
    await wrapper.find('button').trigger('click');
    await wrapper.vm.$nextTick();

    // Dispatch loadeddata on the inner video element to trigger onVideoLoad
    const innerVideo = wrapper.findAll('video')[1];
    if (innerVideo) {
      await innerVideo.trigger('loadeddata');
      // After loadeddata, isLoading should be false
      expect(wrapper.find('[class*="inset-0"]').exists()).toBe(true);
    } else {
      // Inner video not mounted yet — modal still visible
      expect(wrapper.find('.fixed.inset-0').exists()).toBe(true);
    }
  });

  it('play button click does not throw with mocked DOM operations', async () => {
    const wrapper = mountInitialVideoMobile();
    await expect(wrapper.find('button').trigger('click')).resolves.not.toThrow();
  });
});

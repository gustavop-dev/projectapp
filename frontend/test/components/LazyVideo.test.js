import { mount } from '@vue/test-utils';

Object.defineProperty(HTMLVideoElement.prototype, 'play', {
  configurable: true,
  value: jest.fn().mockResolvedValue(undefined),
});
Object.defineProperty(HTMLVideoElement.prototype, 'pause', {
  configurable: true,
  value: jest.fn(),
});
Object.defineProperty(HTMLVideoElement.prototype, 'load', {
  configurable: true,
  value: jest.fn(),
});

jest.mock('../../composables/useIntersectionObserver', () => ({
  useIntersectionObserver: jest.fn(() => ({
    observe: jest.fn((el, cb) => cb()),
    unobserve: jest.fn(),
  })),
}));

jest.mock('../../composables/useAssetCache', () => ({
  useAssetCache: jest.fn(() => ({
    getAsset: jest.fn(() => Promise.resolve(null)),
  })),
}));

import LazyVideo from '../../components/layouts/LazyVideo.vue';

function mountLazyVideo(props = {}) {
  return mount(LazyVideo, {
    props: { src: '/videos/test.mp4', ...props },
  });
}

describe('LazyVideo', () => {
  it('renders the video container', () => {
    const wrapper = mountLazyVideo();

    expect(wrapper.find('.lazy-video-container').exists()).toBe(true);
  });

  it('shows the placeholder before the video loads', () => {
    const wrapper = mountLazyVideo();

    expect(wrapper.find('.placeholder').exists()).toBe(true);
  });

  it('renders the video element', () => {
    const wrapper = mountLazyVideo();

    expect(wrapper.find('video').exists()).toBe(true);
  });

  it('emits loaded event when video loadeddata fires', async () => {
    const wrapper = mountLazyVideo();
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    await wrapper.find('video').trigger('loadeddata');

    expect(wrapper.emitted('loaded')).toBeTruthy();
  });

  it('emits error event when video encounters an error', async () => {
    const wrapper = mountLazyVideo();
    await wrapper.vm.$nextTick();

    await wrapper.find('video').trigger('error');

    expect(wrapper.emitted('error')).toBeTruthy();
  });
});

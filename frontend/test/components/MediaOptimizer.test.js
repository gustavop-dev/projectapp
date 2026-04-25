import { mount } from '@vue/test-utils';

global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.MutationObserver = jest.fn(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
}));

import MediaOptimizer from '../../components/layouts/MediaOptimizer.vue';

function mountMediaOptimizer(props = {}) {
  return mount(MediaOptimizer, { props });
}

describe('MediaOptimizer', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.useRealTimers();
    // Clean up bodyObserver reference
    delete window.bodyObserver;
  });

  it('mounts without errors', () => {
    const wrapper = mountMediaOptimizer();

    expect(wrapper.exists()).toBe(true);
  });

  it('renders a hidden wrapper div', () => {
    const wrapper = mountMediaOptimizer();

    const div = wrapper.find('div[style]');
    expect(div.exists()).toBe(true);
    expect(div.attributes('style')).toContain('display: none');
  });

  it('initializes IntersectionObserver on mount', () => {
    mountMediaOptimizer();

    expect(IntersectionObserver).toHaveBeenCalled();
  });

  it('sets up MutationObserver after initial delay', () => {
    mountMediaOptimizer();

    // Advance past the 1000ms setTimeout that creates MutationObserver,
    // but NOT the 3-min setInterval (which would cause infinite loop with runAllTimers)
    jest.advanceTimersByTime(1100);

    expect(MutationObserver).toHaveBeenCalled();
  });

  // ── lazy loading attributes ────────────────────────────────────────────────

  it('sets loading="lazy" on img elements after 500ms', () => {
    const img = document.createElement('img');
    document.body.appendChild(img);

    mountMediaOptimizer();
    jest.advanceTimersByTime(600);

    expect(img.getAttribute('loading')).toBe('lazy');
    document.body.removeChild(img);
  });

  it('sets decoding="async" on img elements after 500ms', () => {
    const img = document.createElement('img');
    document.body.appendChild(img);

    mountMediaOptimizer();
    jest.advanceTimersByTime(600);

    expect(img.getAttribute('decoding')).toBe('async');
    document.body.removeChild(img);
  });

  it('does not overwrite an existing loading attribute on img elements', () => {
    const img = document.createElement('img');
    img.setAttribute('loading', 'eager');
    document.body.appendChild(img);

    mountMediaOptimizer();
    jest.advanceTimersByTime(600);

    expect(img.getAttribute('loading')).toBe('eager');
    document.body.removeChild(img);
  });

  it('sets preload="metadata" on video elements after 500ms', () => {
    const video = document.createElement('video');
    document.body.appendChild(video);

    mountMediaOptimizer();
    jest.advanceTimersByTime(600);

    expect(video.getAttribute('preload')).toBe('metadata');
    document.body.removeChild(video);
  });

  it('does not overwrite an existing preload attribute on video elements', () => {
    const video = document.createElement('video');
    video.setAttribute('preload', 'auto');
    document.body.appendChild(video);

    mountMediaOptimizer();
    jest.advanceTimersByTime(600);

    expect(video.getAttribute('preload')).toBe('auto');
    document.body.removeChild(video);
  });

  // ── onBeforeUnmount ────────────────────────────────────────────────────────

  it('onBeforeUnmount disconnects the resource observer', () => {
    const wrapper = mountMediaOptimizer();
    const observerInstance = IntersectionObserver.mock.results[IntersectionObserver.mock.results.length - 1].value;

    wrapper.unmount();

    expect(observerInstance.disconnect).toHaveBeenCalled();
  });

  it('onBeforeUnmount disconnects bodyObserver after it is created', () => {
    const wrapper = mountMediaOptimizer();
    jest.advanceTimersByTime(1100);
    const bodyObserverInstance = MutationObserver.mock.results[MutationObserver.mock.results.length - 1].value;

    wrapper.unmount();

    expect(bodyObserverInstance.disconnect).toHaveBeenCalled();
  });

  it('onBeforeUnmount removes the window.bodyObserver reference', () => {
    const wrapper = mountMediaOptimizer();
    jest.advanceTimersByTime(1100);

    wrapper.unmount();

    expect(window.bodyObserver).toBeUndefined();
  });

  // ── cleanup interval ───────────────────────────────────────────────────────

  it('cleanup timer runs after 3 minutes without throwing', () => {
    mountMediaOptimizer();

    expect(() => jest.advanceTimersByTime(3 * 60 * 1000)).not.toThrow();
  });

  // ── IntersectionObserver callback ─────────────────────────────────────────

  it('IntersectionObserver callback handles element without src without throwing', () => {
    const div = document.createElement('div');
    mountMediaOptimizer();

    const ioCallback = IntersectionObserver.mock.calls[0][0];
    expect(() => ioCallback([{ target: div, isIntersecting: true }])).not.toThrow();
  });

  it('IntersectionObserver callback updates inViewport for an already-registered resource', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const img = document.createElement('img');
    img.setAttribute('src', 'tracked.jpg');
    document.body.appendChild(img);

    mountMediaOptimizer();
    const ioCallback = IntersectionObserver.mock.calls[0][0];

    // Register the resource as visible
    ioCallback([{ target: img, isIntersecting: true }]);
    // Update it as not in viewport — exercises the resource.inViewport update branch
    expect(() => ioCallback([{ target: img, isIntersecting: false }])).not.toThrow();

    document.body.removeChild(img);
    consoleSpy.mockRestore();
  });

  it('cleanup interval pauses and clears a video resource that left the viewport', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const video = document.createElement('video');
    video.setAttribute('src', 'movie.mp4');
    video.pause = jest.fn();
    video.load = jest.fn();
    document.body.appendChild(video);

    mountMediaOptimizer();
    const ioCallback = IntersectionObserver.mock.calls[0][0];

    ioCallback([{ target: video, isIntersecting: true }]);
    ioCallback([{ target: video, isIntersecting: false }]);

    jest.advanceTimersByTime(3 * 60 * 1000 + 100);

    expect(video.pause).toHaveBeenCalled();
    expect(video.load).toHaveBeenCalled();

    document.body.removeChild(video);
    consoleSpy.mockRestore();
  });

  // ── MutationObserver callback ─────────────────────────────────────────────

  it('MutationObserver callback observes img elements found inside a newly added node', () => {
    mountMediaOptimizer();
    jest.advanceTimersByTime(1100);

    const moCallback = MutationObserver.mock.calls[0][0];
    const ioInstance = IntersectionObserver.mock.results[0].value;
    const img = document.createElement('img');
    const container = document.createElement('div');
    container.appendChild(img);

    moCallback([{ addedNodes: { forEach: (fn) => fn(container) } }]);

    expect(ioInstance.observe).toHaveBeenCalledWith(img);
  });

  it('MutationObserver callback observes an added node when the node itself is an img', () => {
    mountMediaOptimizer();
    jest.advanceTimersByTime(1100);

    const moCallback = MutationObserver.mock.calls[0][0];
    const ioInstance = IntersectionObserver.mock.results[0].value;
    const img = document.createElement('img');

    moCallback([{ addedNodes: { forEach: (fn) => fn(img) } }]);

    expect(ioInstance.observe).toHaveBeenCalledWith(img);
  });

  // ── onBeforeUnmount resource cleanup ─────────────────────────────────────

  it('onBeforeUnmount pauses VIDEO elements registered in loadedResources', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const video = document.createElement('video');
    video.setAttribute('src', 'clip.mp4');
    video.pause = jest.fn();
    video.load = jest.fn();

    const wrapper = mountMediaOptimizer();
    const ioCallback = IntersectionObserver.mock.calls[0][0];
    ioCallback([{ target: video, isIntersecting: true }]);

    wrapper.unmount();

    expect(video.pause).toHaveBeenCalled();
    expect(video.load).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it('onBeforeUnmount clears the periodic cleanup interval', () => {
    const clearIntervalSpy = jest.spyOn(global, 'clearInterval');
    const wrapper = mountMediaOptimizer();

    wrapper.unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});

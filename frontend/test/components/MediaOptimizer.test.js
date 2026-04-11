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
});

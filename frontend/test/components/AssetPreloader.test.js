import { mount } from '@vue/test-utils';

const mockPreloadAssets = jest.fn().mockResolvedValue(undefined);
const mockCleanExpiredResources = jest.fn().mockResolvedValue(undefined);

jest.mock('../../composables/useAssetCache', () => ({
  useAssetCache: jest.fn(() => ({
    preloadAssets: mockPreloadAssets,
    cleanExpiredResources: mockCleanExpiredResources,
  })),
}));

import AssetPreloader from '../../components/layouts/AssetPreloader.vue';

function mountAssetPreloader(props = {}) {
  return mount(AssetPreloader, { props });
}

describe('AssetPreloader', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockPreloadAssets.mockClear();
    mockCleanExpiredResources.mockClear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('mounts without errors', () => {
    const wrapper = mountAssetPreloader();

    expect(wrapper.exists()).toBe(true);
  });

  it('renders a hidden wrapper div', () => {
    const wrapper = mountAssetPreloader();

    const div = wrapper.find('div[style]');
    expect(div.exists()).toBe(true);
    expect(div.attributes('style')).toContain('display: none');
  });

  it('calls cleanExpiredResources on mount', async () => {
    mountAssetPreloader();

    // Fire the outer setTimeout (requestIdleCallback fallback: 3000ms)
    jest.runAllTimers();
    // Flush the async/await chain inside startPreloading
    await Promise.resolve();
    await Promise.resolve();

    expect(mockCleanExpiredResources).toHaveBeenCalled();
  });

  it('calls preloadAssets when preloadImages prop is provided', async () => {
    mountAssetPreloader({ preloadImages: ['img1.jpg', 'img2.jpg'] });

    // Outer timer → startPreloading() → await cleanExpired... → inner setTimeout(1000)
    jest.runAllTimers();
    await Promise.resolve();
    await Promise.resolve();
    // Fire the inner setTimeout(1000) added after clean completes
    jest.runAllTimers();
    await Promise.resolve();

    expect(mockPreloadAssets).toHaveBeenCalled();
  });
});

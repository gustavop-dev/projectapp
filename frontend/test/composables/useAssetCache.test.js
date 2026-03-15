/**
 * Tests for the useAssetCache composable.
 *
 * Covers: preloadAssets, getAsset, cleanExpiredResources,
 * reactive state (preloadStatus, preloadProgress, preloadedAssets, failedAssets).
 */
let mountedCallbacks;
let useAssetCache;
let MockCacheService;

beforeEach(() => {
  mountedCallbacks = [];

  MockCacheService = jest.fn().mockImplementation(() => ({
    cacheResource: jest.fn().mockResolvedValue(true),
    getResource: jest.fn().mockResolvedValue(null),
    cleanExpiredResources: jest.fn().mockResolvedValue(),
  }));

  jest.resetModules();
  jest.doMock('vue', () => {
    const actualVue = jest.requireActual('vue');
    return {
      ...actualVue,
      onMounted: (cb) => { mountedCallbacks.push(cb); },
    };
  });
  jest.doMock('../../service/CacheService', () => ({
    __esModule: true,
    default: MockCacheService,
  }));
  useAssetCache = require('../../composables/useAssetCache').useAssetCache;

  global.fetch = jest.fn();
});

afterEach(() => {
  delete global.fetch;
  jest.restoreAllMocks();
});

function simulateMount() {
  mountedCallbacks.forEach((cb) => cb());
}

describe('useAssetCache', () => {
  describe('initialization', () => {
    it('returns all expected properties', () => {
      const result = useAssetCache();

      expect(result.preloadStatus.value).toBe('idle');
      expect(result.preloadProgress.value).toBe(0);
      expect(result.preloadedAssets.value).toEqual([]);
      expect(result.failedAssets.value).toEqual([]);
      expect(result.cacheService.value).toBeNull();
    });

    it('initializes CacheService on mount', () => {
      useAssetCache({ cacheName: 'test-cache', expirationTime: 5000 });

      simulateMount();

      expect(MockCacheService).toHaveBeenCalledWith('test-cache', 5000);
    });
  });

  describe('preloadAssets', () => {
    it('preloads assets successfully', async () => {
      global.fetch.mockResolvedValue({ ok: true });
      const { preloadAssets, preloadStatus, preloadedAssets, preloadProgress } = useAssetCache();
      simulateMount();

      await preloadAssets(['https://cdn.example.com/img.png']);

      expect(preloadStatus.value).toBe('success');
      expect(preloadedAssets.value).toContain('https://cdn.example.com/img.png');
      expect(preloadProgress.value).toBe(100);
    });

    it('tracks failed assets', async () => {
      global.fetch.mockResolvedValue({ ok: false });
      const { preloadAssets, failedAssets } = useAssetCache();
      simulateMount();

      await preloadAssets(['https://cdn.example.com/missing.png']);

      expect(failedAssets.value).toContain('https://cdn.example.com/missing.png');
    });

    it('handles fetch errors gracefully', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      global.fetch.mockRejectedValue(new Error('Network error'));
      const { preloadAssets, failedAssets, preloadStatus } = useAssetCache();
      simulateMount();

      await preloadAssets(['https://cdn.example.com/error.png']);

      expect(failedAssets.value).toContain('https://cdn.example.com/error.png');
      expect(preloadStatus.value).toBe('success');
    });

    it('does nothing when cacheService is not initialized', async () => {
      const { preloadAssets, preloadStatus } = useAssetCache();

      await preloadAssets(['https://cdn.example.com/img.png']);

      expect(preloadStatus.value).toBe('idle');
    });

    it('does nothing with empty assets array', async () => {
      const { preloadAssets, preloadStatus } = useAssetCache();
      simulateMount();

      await preloadAssets([]);

      expect(preloadStatus.value).toBe('idle');
    });

    it('does nothing with null assets', async () => {
      const { preloadAssets, preloadStatus } = useAssetCache();
      simulateMount();

      await preloadAssets(null);

      expect(preloadStatus.value).toBe('idle');
    });

    it('calculates progress correctly for multiple assets', async () => {
      global.fetch.mockResolvedValue({ ok: true });
      const { preloadAssets, preloadProgress } = useAssetCache();
      simulateMount();

      await preloadAssets(['a.png', 'b.png']);

      expect(preloadProgress.value).toBe(100);
    });
  });

  describe('getAsset', () => {
    it('returns cached response when available', async () => {
      const cachedResponse = { status: 200 };
      MockCacheService.mockImplementation(() => ({
        cacheResource: jest.fn(),
        getResource: jest.fn().mockResolvedValue(cachedResponse),
        cleanExpiredResources: jest.fn().mockResolvedValue(),
      }));
      jest.resetModules();
      jest.doMock('vue', () => {
        const actualVue = jest.requireActual('vue');
        return { ...actualVue, onMounted: (cb) => { mountedCallbacks.push(cb); } };
      });
      jest.doMock('~/service/CacheService', () => ({ __esModule: true, default: MockCacheService }));
      const { useAssetCache: freshUseAssetCache } = require('../../composables/useAssetCache');

      mountedCallbacks = [];
      const { getAsset } = freshUseAssetCache();
      simulateMount();

      const result = await getAsset('https://cdn.example.com/img.png');

      expect(result).toEqual(cachedResponse);
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('fetches from network and caches when not cached', async () => {
      const networkResponse = { ok: true, clone: jest.fn().mockReturnValue({ ok: true }) };
      global.fetch.mockResolvedValue(networkResponse);
      const { getAsset } = useAssetCache();
      simulateMount();

      const result = await getAsset('https://cdn.example.com/new.png');

      expect(global.fetch).toHaveBeenCalledWith('https://cdn.example.com/new.png');
      expect(result).toEqual(networkResponse);
    });

    it('falls back to fetch when cacheService is null', async () => {
      const networkResponse = { ok: true };
      global.fetch.mockResolvedValue(networkResponse);
      const { getAsset } = useAssetCache();

      const _result = await getAsset('https://cdn.example.com/fallback.png');

      expect(global.fetch).toHaveBeenCalledWith('https://cdn.example.com/fallback.png');
    });

    it('falls back to fetch on cache error', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      MockCacheService.mockImplementation(() => ({
        cacheResource: jest.fn(),
        getResource: jest.fn().mockRejectedValue(new Error('cache error')),
        cleanExpiredResources: jest.fn().mockResolvedValue(),
      }));
      jest.resetModules();
      jest.doMock('vue', () => {
        const actualVue = jest.requireActual('vue');
        return { ...actualVue, onMounted: (cb) => { mountedCallbacks.push(cb); } };
      });
      jest.doMock('~/service/CacheService', () => ({ __esModule: true, default: MockCacheService }));
      const { useAssetCache: freshUseAssetCache } = require('../../composables/useAssetCache');

      mountedCallbacks = [];
      const fetchResponse = { ok: true };
      global.fetch.mockResolvedValue(fetchResponse);
      const { getAsset } = freshUseAssetCache();
      simulateMount();

      const _result = await getAsset('https://cdn.example.com/error.png');

      expect(global.fetch).toHaveBeenCalled();
    });
  });

  describe('onMounted auto-preload', () => {
    it('preloads assets specified in options on mount', async () => {
      global.fetch.mockResolvedValue({ ok: true });
      const { preloadStatus: _preloadStatus } = useAssetCache({
        preloadAssets: ['https://cdn.example.com/auto.png'],
      });
      simulateMount();

      await new Promise(process.nextTick);

      expect(global.fetch).toHaveBeenCalledWith('https://cdn.example.com/auto.png', { cache: 'reload' });
    });
  });

  describe('preloadAssets outer catch', () => {
    it('sets status to error when Promise.allSettled itself throws', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      const originalAllSettled = Promise.allSettled;
      Promise.allSettled = jest.fn().mockRejectedValue(new Error('allSettled failed'));

      const { preloadAssets, preloadStatus } = useAssetCache();
      simulateMount();

      await preloadAssets(['https://cdn.example.com/x.png']);

      expect(preloadStatus.value).toBe('error');
      Promise.allSettled = originalAllSettled;
    });
  });

  describe('cleanExpiredResources', () => {
    it('delegates to cacheService', async () => {
      const { cleanExpiredResources } = useAssetCache();
      simulateMount();

      await expect(cleanExpiredResources()).resolves.toBeUndefined();
    });

    it('does nothing when cacheService is null', async () => {
      const { cleanExpiredResources } = useAssetCache();

      await expect(cleanExpiredResources()).resolves.toBeUndefined();
    });
  });
});

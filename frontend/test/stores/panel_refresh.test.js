/**
 * Tests for the panel_refresh store.
 *
 * Covers: register/unregister, trigger no-op without handler,
 * trigger no-op while already running, isRefreshing toggle in success
 * and error paths.
 */
import { setActivePinia, createPinia } from 'pinia';
import { usePanelRefreshStore } from '../../stores/panel_refresh';

describe('usePanelRefreshStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = usePanelRefreshStore();
  });

  describe('initial state', () => {
    it('has no handler and is not refreshing', () => {
      expect(store.handler).toBeNull();
      expect(store.isRefreshing).toBe(false);
      expect(store.hasHandler).toBe(false);
    });
  });

  describe('register / unregister', () => {
    it('register stores a function and exposes hasHandler=true', () => {
      const fn = jest.fn();
      store.register(fn);
      expect(store.handler).toBe(fn);
      expect(store.hasHandler).toBe(true);
    });

    it('register ignores non-functions', () => {
      store.register('not a function');
      expect(store.handler).toBeNull();
      expect(store.hasHandler).toBe(false);
    });

    it('unregister clears handler and resets isRefreshing', () => {
      store.register(() => {});
      store.isRefreshing = true;
      store.unregister();
      expect(store.handler).toBeNull();
      expect(store.isRefreshing).toBe(false);
    });
  });

  describe('trigger', () => {
    it('is a no-op when no handler is registered', async () => {
      await store.trigger();
      expect(store.isRefreshing).toBe(false);
    });

    it('runs the handler and toggles isRefreshing on success', async () => {
      const fn = jest.fn().mockResolvedValue();
      store.register(fn);
      const promise = store.trigger();
      expect(store.isRefreshing).toBe(true);
      await promise;
      expect(fn).toHaveBeenCalledTimes(1);
      expect(store.isRefreshing).toBe(false);
    });

    it('resets isRefreshing even when handler throws', async () => {
      const fn = jest.fn().mockRejectedValue(new Error('boom'));
      store.register(fn);
      await expect(store.trigger()).rejects.toThrow('boom');
      expect(store.isRefreshing).toBe(false);
    });

    it('is a no-op while a previous trigger is still running', async () => {
      let resolve;
      const fn = jest.fn(() => new Promise((r) => { resolve = r; }));
      store.register(fn);

      const first = store.trigger();
      expect(store.isRefreshing).toBe(true);
      await store.trigger();
      expect(fn).toHaveBeenCalledTimes(1);

      resolve();
      await first;
      expect(store.isRefreshing).toBe(false);
    });
  });
});

/**
 * Tests for the useIntersectionObserver composable.
 *
 * Covers: observe, unobserve, handleIntersect callback,
 * stopObserving behavior, lifecycle mount/unmount cleanup.
 */
let mockObserve;
let mockUnobserve;
let mockDisconnect;
let intersectCallback;
let mountedCallbacks;
let unmountedCallbacks;
let useIntersectionObserver;

class MockIntersectionObserver {
  constructor(callback, _options) {
    intersectCallback = callback;
    this.observe = mockObserve;
    this.unobserve = mockUnobserve;
    this.disconnect = mockDisconnect;
  }
}

beforeEach(() => {
  mockObserve = jest.fn();
  mockUnobserve = jest.fn();
  mockDisconnect = jest.fn();
  intersectCallback = null;
  mountedCallbacks = [];
  unmountedCallbacks = [];
  global.IntersectionObserver = MockIntersectionObserver;

  jest.resetModules();
  jest.doMock('vue', () => {
    const actualVue = jest.requireActual('vue');
    return {
      ...actualVue,
      onMounted: (cb) => { mountedCallbacks.push(cb); },
      onUnmounted: (cb) => { unmountedCallbacks.push(cb); },
    };
  });
  useIntersectionObserver = require('../../composables/useIntersectionObserver').useIntersectionObserver;
});

afterEach(() => {
  delete global.IntersectionObserver;
  jest.restoreAllMocks();
});

function simulateMount() {
  mountedCallbacks.forEach((cb) => cb());
}

function simulateUnmount() {
  unmountedCallbacks.forEach((cb) => cb());
}

describe('useIntersectionObserver', () => {
  describe('initialization', () => {
    it('returns observe, unobserve, and elements', () => {
      const { observe, unobserve, elements } = useIntersectionObserver();

      expect(typeof observe).toBe('function');
      expect(typeof unobserve).toBe('function');
      expect(elements.value).toBeInstanceOf(Map);
    });

    it('accepts custom options', () => {
      const { observe } = useIntersectionObserver({ threshold: 0.5, rootMargin: '50px' });

      expect(typeof observe).toBe('function');
    });
  });

  describe('observe', () => {
    it('adds element to the elements map', () => {
      const { observe, elements } = useIntersectionObserver();
      const el = document.createElement('div');
      const callback = jest.fn();

      observe(el, callback);

      expect(elements.value.has(el)).toBe(true);
      expect(elements.value.get(el).loaded).toBe(false);
      expect(elements.value.get(el).stopObserving).toBe(true);
    });

    it('does nothing when el is null', () => {
      const { observe, elements } = useIntersectionObserver();

      observe(null, jest.fn());

      expect(elements.value.size).toBe(0);
    });

    it('sets stopObserving to false when specified', () => {
      const { observe, elements } = useIntersectionObserver();
      const el = document.createElement('div');

      observe(el, jest.fn(), false);

      expect(elements.value.get(el).stopObserving).toBe(false);
    });

    it('calls observer.observe when observer is initialized', () => {
      const { observe } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');

      observe(el, jest.fn());

      expect(mockObserve).toHaveBeenCalledWith(el);
    });
  });

  describe('unobserve', () => {
    it('does nothing when el is null', () => {
      const { unobserve } = useIntersectionObserver();

      expect(() => unobserve(null)).not.toThrow();
    });

    it('removes element from map and stops observing', () => {
      const { observe, unobserve, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      observe(el, jest.fn());

      unobserve(el);

      expect(elements.value.has(el)).toBe(false);
      expect(mockUnobserve).toHaveBeenCalledWith(el);
    });
  });

  describe('handleIntersect callback', () => {
    it('calls element callback when intersecting', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      const callback = jest.fn();

      observe(el, callback);

      const mockEntries = [{ target: el, isIntersecting: true }];
      intersectCallback(mockEntries, { unobserve: mockUnobserve });

      expect(callback).toHaveBeenCalled();
      expect(elements.value.has(el)).toBe(false);
    });

    it('does not call callback when not intersecting', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      const callback = jest.fn();

      observe(el, callback);

      const mockEntries = [{ target: el, isIntersecting: false }];
      intersectCallback(mockEntries, { unobserve: mockUnobserve });

      expect(callback).not.toHaveBeenCalled();
      expect(elements.value.get(el).loaded).toBe(false);
    });

    it('does not call callback when already loaded', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      const callback = jest.fn();

      observe(el, callback);
      elements.value.get(el).loaded = true;

      const mockEntries = [{ target: el, isIntersecting: true }];
      intersectCallback(mockEntries, { unobserve: mockUnobserve });

      expect(callback).not.toHaveBeenCalled();
    });

    it('keeps observing when stopObserving is false', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      const callback = jest.fn();

      observe(el, callback, false);

      const mockEntries = [{ target: el, isIntersecting: true }];
      intersectCallback(mockEntries, { unobserve: jest.fn() });

      expect(callback).toHaveBeenCalled();
      expect(elements.value.has(el)).toBe(true);
    });

    it('unobserves and removes element when stopObserving is true', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      const localUnobserve = jest.fn();

      observe(el, jest.fn(), true);

      const mockEntries = [{ target: el, isIntersecting: true }];
      intersectCallback(mockEntries, { unobserve: localUnobserve });

      expect(localUnobserve).toHaveBeenCalledWith(el);
      expect(elements.value.has(el)).toBe(false);
    });

    it('ignores entries for unknown elements', () => {
      useIntersectionObserver();
      simulateMount();
      const unknownEl = document.createElement('span');

      const mockEntries = [{ target: unknownEl, isIntersecting: true }];

      expect(() => intersectCallback(mockEntries, { unobserve: jest.fn() })).not.toThrow();
    });
  });

  describe('lifecycle', () => {
    it('observes pre-added elements on mount', () => {
      const { observe } = useIntersectionObserver();
      const el = document.createElement('div');
      observe(el, jest.fn());

      simulateMount();

      expect(mockObserve).toHaveBeenCalledWith(el);
    });

    it('cleans up on unmount', () => {
      const { observe, elements } = useIntersectionObserver();
      simulateMount();
      const el = document.createElement('div');
      observe(el, jest.fn());

      simulateUnmount();

      expect(mockUnobserve).toHaveBeenCalledWith(el);
      expect(mockDisconnect).toHaveBeenCalled();
      expect(elements.value.size).toBe(0);
    });
  });
});

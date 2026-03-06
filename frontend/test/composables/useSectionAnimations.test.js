/**
 * Tests for the useSectionAnimations composable.
 *
 * Covers: initAnimations, cleanup, watcher behavior,
 * animation setup for various data-animate values.
 */
let unmountCallbacks;
let watchCallbacks;
let useSectionAnimations;

const mockScrollTriggerKill = jest.fn();
const mockTimelineKill = jest.fn();
const mockTimeline = {
  to: jest.fn().mockReturnThis(),
  scrollTrigger: { kill: mockScrollTriggerKill },
  kill: mockTimelineKill,
};
const mockGsap = {
  registerPlugin: jest.fn(),
  set: jest.fn(),
  timeline: jest.fn(() => mockTimeline),
};
const mockScrollTriggerClass = {};

beforeEach(() => {
  unmountCallbacks = [];
  watchCallbacks = [];
  jest.clearAllMocks();

  jest.resetModules();
  jest.doMock('vue', () => {
    const actualVue = jest.requireActual('vue');
    return {
      ...actualVue,
      onMounted: (cb) => { /* no-op in tests */ },
      onBeforeUnmount: (cb) => { unmountCallbacks.push(cb); },
      inject: () => actualVue.ref(null),
      watch: (source, cb, opts) => {
        watchCallbacks.push({ source, cb, opts });
      },
    };
  });
  jest.doMock('gsap', () => ({ gsap: mockGsap }));
  jest.doMock('gsap/ScrollTrigger', () => ({ ScrollTrigger: mockScrollTriggerClass }));

  useSectionAnimations = require('../../composables/useSectionAnimations').useSectionAnimations;
});

afterEach(() => {
  jest.restoreAllMocks();
});

const flushPromises = () => new Promise((r) => setTimeout(r, 0));

function createMockSectionRef(animateTypes = []) {
  const { ref } = jest.requireActual('vue');
  const mockEl = {
    querySelectorAll: jest.fn((selector) => {
      const type = selector.match(/data-animate="([^"]+)"/)?.[1];
      if (animateTypes.includes(type)) {
        return [document.createElement('div')];
      }
      return [];
    }),
  };
  return ref(mockEl);
}

describe('useSectionAnimations', () => {
  describe('initialization', () => {
    it('sets up a watcher with immediate option', () => {
      const sectionRef = createMockSectionRef();

      useSectionAnimations(sectionRef);

      expect(watchCallbacks).toHaveLength(1);
      expect(watchCallbacks[0].opts.immediate).toBe(true);
    });

    it('registers onBeforeUnmount callback', () => {
      const sectionRef = createMockSectionRef();

      useSectionAnimations(sectionRef);

      expect(unmountCallbacks).toHaveLength(1);
    });
  });

  describe('initAnimations', () => {
    it('creates timeline when section and tween are present', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.registerPlugin).toHaveBeenCalled();
      expect(mockGsap.timeline).toHaveBeenCalled();
    });

    it('does nothing when sectionRef is null', async () => {
      const { ref } = jest.requireActual('vue');
      const sectionRef = ref(null);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.timeline).not.toHaveBeenCalled();
    });

    it('does nothing when containerTween is falsy', async () => {
      const sectionRef = createMockSectionRef();
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb(null);
      await flushPromises();

      expect(mockGsap.timeline).not.toHaveBeenCalled();
    });

    it('sets initial state for fade-up elements', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, y: 24 })
      );
    });

    it('sets initial state for scale-in elements', async () => {
      const sectionRef = createMockSectionRef(['scale-in']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, scale: 0.92 })
      );
    });

    it('sets initial state for slide-in-left elements', async () => {
      const sectionRef = createMockSectionRef(['slide-in-left']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, x: -40 })
      );
    });

    it('sets initial state for slide-in-right elements', async () => {
      const sectionRef = createMockSectionRef(['slide-in-right']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, x: 40 })
      );
    });

    it('sets initial state for fade-in elements', async () => {
      const sectionRef = createMockSectionRef(['fade-in']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0 })
      );
    });

    it('animates fade-up-stagger children', async () => {
      const { ref } = jest.requireActual('vue');
      const child = document.createElement('span');
      const container = document.createElement('div');
      container.appendChild(child);
      const mockEl = {
        querySelectorAll: jest.fn((selector) => {
          const type = selector.match(/data-animate="([^"]+)"/)?.[1];
          if (type === 'fade-up-stagger') return [container];
          return [];
        }),
      };
      const sectionRef = ref(mockEl);

      useSectionAnimations(sectionRef);
      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, y: 18 })
      );
    });

    it('animates timeline.to for fade-up elements', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockTimeline.to).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 1, y: 0, duration: 0.7 }),
        0
      );
    });
  });

  describe('cleanup', () => {
    it('kills timeline on unmount', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);
      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      unmountCallbacks.forEach((cb) => cb());

      expect(mockTimelineKill).toHaveBeenCalled();
      expect(mockScrollTriggerKill).toHaveBeenCalled();
    });

    it('handles cleanup when no timeline exists', () => {
      const sectionRef = createMockSectionRef();
      useSectionAnimations(sectionRef);

      expect(() => unmountCallbacks.forEach((cb) => cb())).not.toThrow();
    });

    it('calls cleanup before re-initializing', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();
      const killCountAfterFirst = mockTimelineKill.mock.calls.length;

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockTimelineKill.mock.calls.length).toBeGreaterThan(killCountAfterFirst);
    });
  });
});

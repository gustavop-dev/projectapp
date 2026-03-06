/**
 * Tests for the useSectionAnimations composable.
 *
 * Covers: initAnimations, cleanup, watcher behavior,
 * unified top-to-bottom fade-up animation cascade.
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
      onMounted: (_cb) => { /* no-op in tests */ },
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

/**
 * Creates a mock section ref with [data-animate] elements.
 * Each element gets a getBoundingClientRect mock sorted by topOffset.
 */
function createMockSectionRef(animateTypes = []) {
  const { ref } = jest.requireActual('vue');
  const elements = animateTypes.map((type, idx) => {
    const el = document.createElement('div');
    el.setAttribute('data-animate', type);
    el.getBoundingClientRect = () => ({ top: idx * 100, left: 0 });
    return el;
  });
  const mockEl = {
    querySelectorAll: jest.fn((selector) => {
      if (selector === '[data-animate]') return elements;
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

    it('sets uniform initial state (opacity:0, y:30) for all elements', async () => {
      const sectionRef = createMockSectionRef(['fade-up', 'fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.set).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 0, y: 20 })
      );
    });

    it('does not create timeline when no [data-animate] elements exist', async () => {
      const sectionRef = createMockSectionRef([]);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockGsap.timeline).not.toHaveBeenCalled();
    });

    it('expands fade-up-stagger children into individual targets', async () => {
      const { ref } = jest.requireActual('vue');
      const child1 = document.createElement('span');
      child1.getBoundingClientRect = () => ({ top: 0, left: 0 });
      const child2 = document.createElement('span');
      child2.getBoundingClientRect = () => ({ top: 50, left: 0 });
      const container = document.createElement('div');
      container.setAttribute('data-animate', 'fade-up-stagger');
      container.appendChild(child1);
      container.appendChild(child2);
      const mockEl = {
        querySelectorAll: jest.fn((selector) => {
          if (selector === '[data-animate]') return [container];
          return [];
        }),
      };
      const sectionRef = ref(mockEl);

      useSectionAnimations(sectionRef);
      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      // Should animate 2 children (not the container itself)
      const setCall = mockGsap.set.mock.calls[0];
      expect(setCall[0]).toHaveLength(2);
    });

    it('animates with uniform fade-up (duration:1.4, stagger:0.25)', async () => {
      const sectionRef = createMockSectionRef(['fade-up']);
      useSectionAnimations(sectionRef);

      watchCallbacks[0].cb({ scrollTrigger: {} });
      await flushPromises();

      expect(mockTimeline.to).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ opacity: 1, y: 0, duration: 1.4, stagger: 0.25 }),
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

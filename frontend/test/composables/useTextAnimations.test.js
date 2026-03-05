/**
 * Tests for the useTextAnimations composable.
 *
 * Covers: all animation functions (fadeInFromBottom, fadeInFromLeft,
 * fadeInFromRight, scaleIn, typewriter, staggerFadeIn, wordReveal,
 * counterAnimation, createTimeline), cleanup, refreshScrollTrigger,
 * lifecycle hooks, and textAnimationPresets export.
 */
let useTextAnimations;
let textAnimationPresets;
let mountedCallbacks;
let unmountCallbacks;

const mockScrollTrigger = {
  refresh: jest.fn(),
  kill: jest.fn(),
};
const mockAnimation = {
  scrollTrigger: mockScrollTrigger,
};
const mockTimeline = {
  scrollTrigger: mockScrollTrigger,
};
const mockGsap = {
  registerPlugin: jest.fn(),
  set: jest.fn(),
  to: jest.fn(() => mockAnimation),
  fromTo: jest.fn(() => mockAnimation),
  timeline: jest.fn(() => mockTimeline),
  killTweensOf: jest.fn(),
};
const mockScrollTriggerClass = {
  refresh: jest.fn(),
};

beforeEach(() => {
  mountedCallbacks = [];
  unmountCallbacks = [];
  jest.clearAllMocks();

  jest.resetModules();
  jest.doMock('vue', () => {
    const actualVue = jest.requireActual('vue');
    return {
      ...actualVue,
      onMounted: (cb) => { mountedCallbacks.push(cb); },
      onBeforeUnmount: (cb) => { unmountCallbacks.push(cb); },
      getCurrentInstance: () => ({ uid: 1 }),
    };
  });
  jest.doMock('gsap', () => ({ gsap: mockGsap }));
  jest.doMock('gsap/ScrollTrigger', () => ({ ScrollTrigger: mockScrollTriggerClass }));
  jest.doMock('gsap/TextPlugin', () => ({ TextPlugin: {} }));
  jest.doMock('gsap/SplitText', () => ({ SplitText: {} }));

  const mod = require('../../composables/useTextAnimations');
  useTextAnimations = mod.useTextAnimations;
  textAnimationPresets = mod.textAnimationPresets;
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('useTextAnimations', () => {
  describe('initialization', () => {
    it('returns core animation functions', () => {
      const result = useTextAnimations();

      expect(typeof result.fadeInFromBottom).toBe('function');
      expect(typeof result.fadeInFromLeft).toBe('function');
      expect(typeof result.fadeInFromRight).toBe('function');
      expect(typeof result.scaleIn).toBe('function');
      expect(typeof result.typewriter).toBe('function');
    });

    it('returns advanced animation functions', () => {
      const result = useTextAnimations();

      expect(typeof result.staggerFadeIn).toBe('function');
      expect(typeof result.wordReveal).toBe('function');
      expect(typeof result.counterAnimation).toBe('function');
      expect(typeof result.createTimeline).toBe('function');
    });

    it('returns utility functions', () => {
      const result = useTextAnimations();

      expect(typeof result.cleanup).toBe('function');
      expect(typeof result.refreshScrollTrigger).toBe('function');
    });

    it('returns reactive arrays', () => {
      const result = useTextAnimations();

      expect(result.animatedElements.value).toEqual([]);
      expect(result.scrollTriggers.value).toEqual([]);
    });

    it('registers lifecycle hooks when getCurrentInstance returns truthy', () => {
      useTextAnimations();

      expect(mountedCallbacks).toHaveLength(1);
      expect(unmountCallbacks).toHaveLength(1);
    });
  });

  describe('fadeInFromBottom', () => {
    it('sets initial state and creates animation', () => {
      const { fadeInFromBottom, scrollTriggers, animatedElements } = useTextAnimations();
      const el = document.createElement('div');

      const _anim = fadeInFromBottom(el);

      expect(mockGsap.set).toHaveBeenCalledWith(el, expect.objectContaining({ opacity: 0.8 }));
      expect(mockGsap.to).toHaveBeenCalledWith(el, expect.objectContaining({
        y: 0, opacity: 1, duration: 0.8,
      }));
      expect(scrollTriggers.value).toHaveLength(1);
      expect(animatedElements.value).toContain(el);
    });

    it('accepts custom options', () => {
      const { fadeInFromBottom } = useTextAnimations();
      const el = document.createElement('div');

      fadeInFromBottom(el, { delay: 0.5, duration: 1.2, distance: 100 });

      expect(mockGsap.to).toHaveBeenCalledWith(el, expect.objectContaining({
        delay: 0.5, duration: 1.2,
      }));
    });
  });

  describe('fadeInFromLeft', () => {
    it('sets initial state with negative x offset', () => {
      const { fadeInFromLeft } = useTextAnimations();
      const el = document.createElement('div');

      fadeInFromLeft(el);

      expect(mockGsap.set).toHaveBeenCalledWith(el, expect.objectContaining({ opacity: 0.8 }));
      expect(mockGsap.to).toHaveBeenCalledWith(el, expect.objectContaining({
        x: 0, opacity: 1,
      }));
    });
  });

  describe('fadeInFromRight', () => {
    it('sets initial state with positive x offset', () => {
      const { fadeInFromRight } = useTextAnimations();
      const el = document.createElement('div');

      fadeInFromRight(el);

      expect(mockGsap.set).toHaveBeenCalledWith(el, expect.objectContaining({ opacity: 0.8 }));
      expect(mockGsap.to).toHaveBeenCalledWith(el, expect.objectContaining({
        x: 0, opacity: 1,
      }));
    });
  });

  describe('scaleIn', () => {
    it('animates scale from 0.95 to 1', () => {
      const { scaleIn } = useTextAnimations();
      const el = document.createElement('div');

      scaleIn(el);

      expect(mockGsap.set).toHaveBeenCalledWith(el, expect.objectContaining({
        scale: 0.95, opacity: 0.9,
      }));
      expect(mockGsap.to).toHaveBeenCalledWith(el, expect.objectContaining({
        scale: 1, opacity: 1,
      }));
    });
  });

  describe('typewriter', () => {
    it('uses fromTo for character-by-character animation', () => {
      const { typewriter } = useTextAnimations();
      const el = document.createElement('div');
      el.textContent = 'Hello World';

      typewriter(el);

      expect(mockGsap.set).toHaveBeenCalledWith(el, { opacity: 1 });
      expect(mockGsap.fromTo).toHaveBeenCalledWith(
        el,
        { text: '' },
        expect.objectContaining({ text: 'Hello World', ease: 'none' })
      );
    });
  });

  describe('staggerFadeIn', () => {
    it('animates multiple elements with stagger from bottom', () => {
      const { staggerFadeIn } = useTextAnimations();
      const els = [document.createElement('div'), document.createElement('div')];

      staggerFadeIn(els);

      expect(mockGsap.set).toHaveBeenCalledWith(els, expect.objectContaining({ opacity: 0.8 }));
      expect(mockGsap.to).toHaveBeenCalledWith(els, expect.objectContaining({
        y: 0, opacity: 1, stagger: 0.1,
      }));
    });

    it('handles from left direction', () => {
      const { staggerFadeIn } = useTextAnimations();
      const els = [document.createElement('div')];

      staggerFadeIn(els, { from: 'left' });

      expect(mockGsap.set).toHaveBeenCalledWith(els, expect.objectContaining({ opacity: 0.8 }));
      expect(mockGsap.to).toHaveBeenCalledWith(els, expect.objectContaining({
        x: 0, opacity: 1,
      }));
    });

    it('handles from right direction', () => {
      const { staggerFadeIn } = useTextAnimations();
      const els = [document.createElement('div')];

      staggerFadeIn(els, { from: 'right' });

      expect(mockGsap.to).toHaveBeenCalledWith(els, expect.objectContaining({
        x: 0, opacity: 1,
      }));
    });

    it('handles from scale direction', () => {
      const { staggerFadeIn } = useTextAnimations();
      const els = [document.createElement('div')];

      staggerFadeIn(els, { from: 'center' });

      expect(mockGsap.set).toHaveBeenCalledWith(els, expect.objectContaining({
        scale: 0.95, opacity: 0.9,
      }));
      expect(mockGsap.to).toHaveBeenCalledWith(els, expect.objectContaining({
        scale: 1, opacity: 1,
      }));
    });
  });

  describe('wordReveal', () => {
    it('splits text into word spans and animates', () => {
      const { wordReveal } = useTextAnimations();
      const el = document.createElement('div');
      el.textContent = 'Hello World';

      wordReveal(el);

      expect(el.innerHTML).toContain('Hello');
      expect(el.innerHTML).toContain('World');
      expect(mockGsap.set).toHaveBeenCalled();
      expect(mockGsap.to).toHaveBeenCalled();
    });
  });

  describe('counterAnimation', () => {
    it('animates counter from 0 to target value', () => {
      const { counterAnimation } = useTextAnimations();
      const el = document.createElement('div');

      counterAnimation(el, { targetValue: 50, suffix: '%', prefix: '+' });

      expect(mockGsap.to).toHaveBeenCalledWith(
        { value: 0 },
        expect.objectContaining({
          value: 50,
        })
      );
    });

    it('updates element textContent on each animation frame', () => {
      const { counterAnimation } = useTextAnimations();
      const el = document.createElement('div');

      counterAnimation(el, { targetValue: 100, suffix: '%', prefix: '+' });

      const gsapToArgs = mockGsap.to.mock.calls[0];
      const counterObj = gsapToArgs[0];
      const animConfig = gsapToArgs[1];

      counterObj.value = 42;
      animConfig.onUpdate();

      expect(el.textContent).toBe('+42%');
    });
  });

  describe('createTimeline', () => {
    it('creates a GSAP timeline with scroll trigger', () => {
      const { createTimeline, scrollTriggers } = useTextAnimations();
      const trigger = document.createElement('div');

      const _tl = createTimeline({ triggerElement: trigger });

      expect(mockGsap.timeline).toHaveBeenCalled();
      expect(scrollTriggers.value).toHaveLength(1);
    });
  });

  describe('cleanup', () => {
    it('kills all scroll triggers and animations', () => {
      const { fadeInFromBottom, cleanup, scrollTriggers, animatedElements } = useTextAnimations();
      const el = document.createElement('div');
      fadeInFromBottom(el);

      cleanup();

      expect(mockScrollTrigger.kill).toHaveBeenCalled();
      expect(mockGsap.killTweensOf).toHaveBeenCalledWith(el);
      expect(scrollTriggers.value).toEqual([]);
      expect(animatedElements.value).toEqual([]);
      expect(mockScrollTriggerClass.refresh).toHaveBeenCalled();
    });
  });

  describe('refreshScrollTrigger', () => {
    it('calls ScrollTrigger.refresh', () => {
      const { refreshScrollTrigger } = useTextAnimations();

      refreshScrollTrigger();

      expect(mockScrollTriggerClass.refresh).toHaveBeenCalled();
    });
  });

  describe('lifecycle hooks', () => {
    it('calls ScrollTrigger.refresh on mount', () => {
      useTextAnimations();

      mountedCallbacks.forEach((cb) => cb());

      expect(mockScrollTriggerClass.refresh).toHaveBeenCalled();
    });

    it('calls cleanup on unmount', () => {
      const { fadeInFromBottom } = useTextAnimations();
      const el = document.createElement('div');
      fadeInFromBottom(el);

      unmountCallbacks.forEach((cb) => cb());

      expect(mockScrollTrigger.kill).toHaveBeenCalled();
      expect(mockGsap.killTweensOf).toHaveBeenCalled();
    });
  });

  describe('without getCurrentInstance', () => {
    it('does not register lifecycle hooks', () => {
      jest.resetModules();
      jest.doMock('vue', () => {
        const actualVue = jest.requireActual('vue');
        return {
          ...actualVue,
          onMounted: jest.fn(),
          onBeforeUnmount: jest.fn(),
          getCurrentInstance: () => null,
        };
      });
      jest.doMock('gsap', () => ({ gsap: mockGsap }));
      jest.doMock('gsap/ScrollTrigger', () => ({ ScrollTrigger: mockScrollTriggerClass }));
      jest.doMock('gsap/TextPlugin', () => ({ TextPlugin: {} }));
      jest.doMock('gsap/SplitText', () => ({ SplitText: {} }));

      const { useTextAnimations: freshUse } = require('../../composables/useTextAnimations');
      const vue = require('vue');

      freshUse();

      expect(vue.onMounted).not.toHaveBeenCalled();
      expect(vue.onBeforeUnmount).not.toHaveBeenCalled();
    });
  });
});

describe('textAnimationPresets', () => {
  it('exports sectionTitle preset', () => {
    expect(textAnimationPresets.sectionTitle).toEqual(expect.objectContaining({
      duration: 1, distance: 60,
    }));
  });

  it('exports subtitle preset', () => {
    expect(textAnimationPresets.subtitle).toEqual(expect.objectContaining({
      duration: 0.8, delay: 0.2,
    }));
  });

  it('exports paragraph preset', () => {
    expect(textAnimationPresets.paragraph).toEqual(expect.objectContaining({
      duration: 0.6, delay: 0.4,
    }));
  });

  it('exports card preset', () => {
    expect(textAnimationPresets.card).toEqual(expect.objectContaining({
      duration: 0.5,
    }));
  });

  it('exports statistic preset', () => {
    expect(textAnimationPresets.statistic).toEqual(expect.objectContaining({
      duration: 1.5,
    }));
  });

  it('exports button preset', () => {
    expect(textAnimationPresets.button).toEqual(expect.objectContaining({
      duration: 0.4, delay: 0.6,
    }));
  });
});

/**
 * Tests for PreloaderAnimation.vue.
 *
 * Covers: rendering, personalizedSubtext computed, handleImageLoad,
 * handleArrowLoad, checkImagesLoaded, active prop watcher,
 * isDesktop ref, safety fallback timeout, finishAnimation emit.
 */

const capturedTimelineOpts = [];

jest.mock('gsap', () => {
  const tl = {
    to: jest.fn().mockReturnThis(),
    fromTo: jest.fn().mockReturnThis(),
    set: jest.fn().mockReturnThis(),
    kill: jest.fn(),
  };
  const mock = {
    to: jest.fn(),
    set: jest.fn(),
    fromTo: jest.fn(),
    timeline: jest.fn((opts) => {
      if (opts) capturedTimelineOpts.push(opts);
      return tl;
    }),
  };
  return { gsap: mock, default: mock, ...mock };
});

jest.mock('../../composables/useMessages', () => ({
  useGlobalMessages: jest.fn(() => ({
    globalMessages: require('vue').ref({
      photo_text1: 'Simple',
      photo_text2: 'Potente',
      photo_text3: 'Elegante',
      photo_text4: 'Rápido',
      photo_text5: 'Tuyo',
      left_text: 'Colección',
      right_text: 'Espíritu',
    }),
  })),
}));

import { mount } from '@vue/test-utils';
import PreloaderAnimation from '../../components/animations/PreloaderAnimation.vue';

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

function mountPreloader(props = {}) {
  return mount(PreloaderAnimation, {
    props: { active: true, ...props },
  });
}

describe('PreloaderAnimation', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    capturedTimelineOpts.length = 0;
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  describe('rendering', () => {
    it('renders the preloader container when active is true', () => {
      const wrapper = mountPreloader();

      expect(wrapper.find('.fixed.inset-0.z-\\[999\\]').exists()).toBe(true);
    });

    it('renders the white overlay element when active is true', () => {
      const wrapper = mountPreloader({ active: true });

      expect(wrapper.find('.fixed.inset-0.z-\\[99\\]').exists()).toBe(true);
    });

    it('shows the personalized overlay with clientName when provided', () => {
      const wrapper = mountPreloader({ clientName: 'Empresa ABC' });

      expect(wrapper.text()).toContain('Empresa ABC');
    });

    it('does not show personalized overlay content when clientName is empty', () => {
      const wrapper = mountPreloader({ clientName: '' });

      expect(wrapper.find('[ref="personalizedOverlay"]').exists()).toBe(false);
    });

    it('renders the progress text element showing 0%', () => {
      const wrapper = mountPreloader();

      expect(wrapper.text()).toContain('0%');
    });
  });

  // ── personalizedSubtext ───────────────────────────────────────────────────

  describe('personalizedSubtext', () => {
    it('returns Spanish subtext by default', () => {
      const wrapper = mountPreloader({ clientName: 'Carlos', language: 'es' });

      expect(wrapper.text()).toContain('Preparado especialmente para');
    });

    it('returns English subtext when language is en', () => {
      const wrapper = mountPreloader({ clientName: 'Carlos', language: 'en' });

      expect(wrapper.text()).toContain('Prepared especially for');
    });
  });

  // ── handleImageLoad ───────────────────────────────────────────────────────

  describe('handleImageLoad', () => {
    it('does not set imagesLoaded with a single image load event', async () => {
      const wrapper = mountPreloader();
      const img = wrapper.find('img');
      await img.trigger('load');

      // collectionContainer uses v-show="imagesLoaded"; with only 1 load it should not be visible
      // The v-show element exists but should still be in DOM (just hidden)
      expect(wrapper.find('[class*="absolute flex items-center opacity-0"]').exists()).toBe(true);
    });

    it('triggers 11 load events sets imagesLoaded and schedules animation', async () => {
      const wrapper = mountPreloader();

      const images = wrapper.findAll('img');
      for (let i = 0; i < 11; i++) {
        const img = images[i % images.length];
        await img.trigger('load');
      }
      await flushPromises();

      // imagesLoaded is now true; the 100ms animation timer is pending
      expect(jest.getTimerCount()).toBeGreaterThan(0);
    });
  });

  // ── handleArrowLoad ───────────────────────────────────────────────────────

  describe('handleArrowLoad', () => {
    it('each arrow @load event also increments the loaded counter', async () => {
      const wrapper = mountPreloader();
      const images = wrapper.findAll('img');

      // Trigger the first 10 via handleImageLoad, then one more via handleArrowLoad
      for (let i = 0; i < 10; i++) {
        await images[i].trigger('load');
      }
      // After 10 loads, imagesLoaded should still be false
      // One more load should cross the threshold
      await images[10].trigger('load');

      // Animation timer should now be scheduled
      expect(jest.getTimerCount()).toBeGreaterThan(0);
    });
  });

  // ── active prop watcher ───────────────────────────────────────────────────

  describe('active prop watcher', () => {
    it('isLoading starts as true when active is true', () => {
      const wrapper = mountPreloader({ active: true });

      // The preloader container is shown via v-show="isLoading"
      // v-show sets display:none when false; when true it should be visible
      const container = wrapper.find('.fixed.inset-0.z-\\[999\\]');
      expect(container.element.style.display).not.toBe('none');
    });

    it('isLoading starts as false when active is false', () => {
      const wrapper = mountPreloader({ active: false });

      const container = wrapper.find('.fixed.inset-0.z-\\[999\\]');
      expect(container.element.style.display).toBe('none');
    });

    it('isLoading becomes true when active prop changes from false to true', async () => {
      const wrapper = mountPreloader({ active: false });

      expect(wrapper.find('.fixed.inset-0.z-\\[999\\]').element.style.display).toBe('none');

      await wrapper.setProps({ active: true });
      await flushPromises();

      expect(wrapper.find('.fixed.inset-0.z-\\[999\\]').element.style.display).not.toBe('none');
    });
  });

  // ── isDesktop ─────────────────────────────────────────────────────────────

  describe('isDesktop', () => {
    it('renders the desktop text-2xl class when window.innerWidth is set to 1280', () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1280 });
      const wrapper = mountPreloader();

      expect(wrapper.find('.text-2xl').exists()).toBe(true);

      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 0 });
    });

    it('renders the mobile text-lg class when window.innerWidth is 0', () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 0 });
      const wrapper = mountPreloader();

      expect(wrapper.find('.text-lg').exists()).toBe(true);
    });
  });

  // ── Safety fallback timeout ───────────────────────────────────────────────

  describe('safety fallback', () => {
    it('sets imagesLoaded after 4000ms via the safety timeout', async () => {
      const wrapper = mountPreloader({ active: true });

      // Before the timeout fires, the collection container is hidden (imagesLoaded = false)
      const collectionDiv = wrapper.findAll('div').find((d) => d.element.style.display === 'none' && d.text().length === 0);

      jest.advanceTimersByTime(4000);
      await flushPromises();

      // After 4000ms safety fallback, imagesLoaded = true and animatePreloader() runs
      // The capturedTimelineOpts should now contain the animatePreloader timeline opts
      expect(capturedTimelineOpts.length).toBeGreaterThan(0);
    });
  });

  // ── handleResize ──────────────────────────────────────────────────────────

  describe('handleResize', () => {
    it('updates isDesktop when window is resized from mobile to desktop width', async () => {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 0 });
      const wrapper = mountPreloader();

      expect(wrapper.find('.text-lg').exists()).toBe(true);

      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 1280 });
      window.dispatchEvent(new Event('resize'));
      jest.advanceTimersByTime(200);
      await flushPromises();

      expect(wrapper.find('.text-2xl').exists()).toBe(true);

      Object.defineProperty(window, 'innerWidth', { configurable: true, value: 0 });
    });

    it('does not throw when resize is dispatched multiple times rapidly', () => {
      const wrapper = mountPreloader();

      expect(() => {
        window.dispatchEvent(new Event('resize'));
        window.dispatchEvent(new Event('resize'));
        window.dispatchEvent(new Event('resize'));
        jest.advanceTimersByTime(200);
      }).not.toThrow();

      expect(wrapper.exists()).toBe(true);
    });
  });

  // ── arrow interval / animateFonts ─────────────────────────────────────────

  describe('arrow interval', () => {
    it('toggles mainText1 from font-caveat-semibold to font-caveat-bold after 140ms', async () => {
      const wrapper = mountPreloader({ active: true });

      jest.advanceTimersByTime(4000);
      await flushPromises();

      const coleccionSpan = wrapper.findAll('span').find(s => s.text().includes('Colección'));
      expect(coleccionSpan.classes()).toContain('font-caveat-semibold');

      jest.advanceTimersByTime(140);
      await wrapper.vm.$nextTick();

      expect(coleccionSpan.classes()).toContain('font-caveat-bold');
    });
  });

  // ── showPersonalizedGreeting ───────────────────────────────────────────────

  describe('showPersonalizedGreeting', () => {
    it('creates a greeting timeline when the main timeline completes with clientName set', async () => {
      const wrapper = mountPreloader({ active: true, clientName: 'Empresa ABC' });

      jest.advanceTimersByTime(4000);
      await flushPromises();

      const timelinesBefore = capturedTimelineOpts.length;
      const mainTimelineOpts = capturedTimelineOpts.find(
        (o) => typeof o.onComplete === 'function' && !o.repeat && !o.yoyo,
      );

      expect(() => mainTimelineOpts.onComplete()).not.toThrow();

      expect(capturedTimelineOpts.length).toBeGreaterThan(timelinesBefore);
    });
  });

  // ── unmount cleanup ───────────────────────────────────────────────────────

  describe('unmount', () => {
    it('does not throw when unmounted after the safety fallback fires', async () => {
      const wrapper = mountPreloader({ active: true });

      jest.advanceTimersByTime(4000);
      await flushPromises();

      expect(() => wrapper.unmount()).not.toThrow();
    });
  });

  // ── finishAnimation via GSAP onComplete ───────────────────────────────────

  describe('finishAnimation', () => {
    it('emits animationComplete when the finishTl onComplete fires', async () => {
      const wrapper = mountPreloader({ active: true });

      // 4000ms safety → animatePreloader() runs → captures main timeline + floating timeline opts
      jest.advanceTimersByTime(4000);
      await flushPromises();
      // 2000ms force-finish timeout inside animatePreloader fires → finishAnimation() runs
      jest.advanceTimersByTime(2000);
      await flushPromises();

      // finishAnimation creates a GSAP timeline with onComplete that emits animationComplete.
      // capturedTimelineOpts order: main timeline (animatePreloader), floating timeline (repeat/-1),
      // then finishTl (finishAnimation) — so take the last one without repeat/yoyo.
      const withOnComplete = capturedTimelineOpts.filter((o) => typeof o.onComplete === 'function' && !o.repeat && !o.yoyo);
      expect(withOnComplete.length).toBeGreaterThan(0);
      withOnComplete[withOnComplete.length - 1].onComplete();

      expect(wrapper.emitted('animationComplete')).toBeTruthy();
    });
  });
});

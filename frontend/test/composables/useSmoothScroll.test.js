/**
 * Tests for the useSmoothScroll composable.
 *
 * Covers: smoothScrollTo easing animation, smoothScrollToElement viewport offset,
 * no-op for zero distance, promise resolution, and edge cases.
 */

let pendingRaf = null;

let _scrollY = 0;

beforeEach(() => {
  pendingRaf = null;
  _scrollY = 0;
  Object.defineProperty(window, 'scrollY', { get: () => _scrollY, configurable: true });
  window.innerHeight = 800;
  jest.spyOn(window, 'scrollTo').mockImplementation((x, y) => {
    _scrollY = y;
  });
  jest.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
    pendingRaf = cb;
    return 1;
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

/**
 * Tick one rAF frame at the given timestamp.
 * Each call processes exactly one pending callback.
 */
function tickRAF(timestamp) {
  const cb = pendingRaf;
  pendingRaf = null;
  if (cb) cb(timestamp);
}

/**
 * Run rAF frames from t=start to t=end in 16ms steps.
 */
function runFrames(start, end, step = 16) {
  for (let t = start; t <= end; t += step) {
    tickRAF(t);
  }
}

const { smoothScrollTo, smoothScrollToElement } = require('../../composables/useSmoothScroll');

describe('smoothScrollTo', () => {
  it('resolves immediately when distance is zero', async () => {
    _scrollY = 500;
    const promise = smoothScrollTo(500, 600);
    await promise;
    expect(window.requestAnimationFrame).not.toHaveBeenCalled();
  });

  it('resolves immediately when distance is less than 1px', async () => {
    _scrollY = 100;
    const promise = smoothScrollTo(100.5, 600);
    await promise;
    expect(window.requestAnimationFrame).not.toHaveBeenCalled();
  });

  it('scrolls to target position over time using rAF', async () => {
    _scrollY = 0;

    const promise = smoothScrollTo(600, 600);

    // First frame sets startTime; easeOutCubic(0) = 0 → scrollTo(0, 0)
    tickRAF(1000);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 0);

    // At t=1300 (half of 600ms): easeOutCubic(0.5) = 1 - 0.125 = 0.875 → 525
    tickRAF(1300);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 525);

    // At t=1600 (end): progress=1 → scrollTo(0, 600)
    tickRAF(1600);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 600);

    await promise;
  });

  it('clamps progress at 1.0 for timestamps past duration', async () => {
    _scrollY = 0;
    const promise = smoothScrollTo(1000, 500);

    // First frame
    tickRAF(100);

    // Frame well past end (100 + 1000 > 100 + 500)
    tickRAF(1100);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 1000);

    await promise;
  });

  it('scrolls upward correctly (negative distance)', async () => {
    _scrollY = 800;

    const promise = smoothScrollTo(0, 600);

    // First frame at t=0: captures start, progress=0 → stays at 800
    tickRAF(0);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 800);

    // End frame: progress=1 → scroll to 0
    tickRAF(600);
    expect(window.scrollTo).toHaveBeenLastCalledWith(0, 0);

    await promise;
  });
});

describe('smoothScrollToElement', () => {
  it('calculates target position based on element rect and viewport offset', async () => {
    _scrollY = 100;
    window.innerHeight = 800;

    const mockEl = {
      getBoundingClientRect: () => ({ top: 400, left: 0, width: 200, height: 50, bottom: 450, right: 200 }),
    };

    const promise = smoothScrollToElement(mockEl, { duration: 600, viewportOffset: 0.15 });

    // targetY = 100 + 400 - 800*0.15 = 380. Distance = 380 - 100 = 280
    expect(pendingRaf).not.toBeNull();

    // Run full animation
    runFrames(0, 700);

    await promise;
    expect(_scrollY).toBe(380);
  });

  it('clamps targetY to 0 when element is near the top', async () => {
    _scrollY = 0;
    window.innerHeight = 800;

    const mockEl = {
      getBoundingClientRect: () => ({ top: 50, left: 0, width: 200, height: 50, bottom: 100, right: 200 }),
    };

    const promise = smoothScrollToElement(mockEl, { duration: 600, viewportOffset: 0.15 });

    // targetY = 0 + 50 - 120 = -70 → clamped to 0. Distance = 0 → immediate resolve
    await promise;
    expect(_scrollY).toBe(0);
  });

  it('uses default options when none provided', async () => {
    _scrollY = 0;
    window.innerHeight = 1000;

    const mockEl = {
      getBoundingClientRect: () => ({ top: 500, left: 0, width: 200, height: 50, bottom: 550, right: 200 }),
    };

    const promise = smoothScrollToElement(mockEl);

    // Default viewportOffset=0.15, duration=600 → targetY = 0 + 500 - 150 = 350
    expect(pendingRaf).not.toBeNull();

    runFrames(0, 700);

    await promise;
    expect(_scrollY).toBe(350);
  });
});

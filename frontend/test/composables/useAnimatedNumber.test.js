/**
 * Tests for the useAnimatedNumber composable.
 *
 * Covers: initial value, animation on target change, same-value no-op,
 * cancellation of in-flight animation, null/undefined target handling.
 */
import { ref, nextTick } from 'vue';
import { useAnimatedNumber } from '../../composables/useAnimatedNumber';

describe('useAnimatedNumber', () => {
  let rafCallbacks;
  let rafId;

  beforeEach(() => {
    rafCallbacks = [];
    rafId = 0;
    jest.spyOn(global, 'requestAnimationFrame').mockImplementation((cb) => {
      rafId += 1;
      rafCallbacks.push({ id: rafId, cb });
      return rafId;
    });
    jest.spyOn(global, 'cancelAnimationFrame').mockImplementation((id) => {
      rafCallbacks = rafCallbacks.filter((r) => r.id !== id);
    });
    jest.spyOn(performance, 'now').mockReturnValue(0);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  function flushRaf(time) {
    performance.now.mockReturnValue(time);
    const pending = [...rafCallbacks];
    rafCallbacks = [];
    pending.forEach((r) => r.cb(time));
  }

  it('returns initial target value as animated value', () => {
    const target = ref(42);
    const { animated } = useAnimatedNumber(target);

    expect(animated.value).toBe(42);
  });

  it('returns 0 when target starts as null', () => {
    const target = ref(null);
    const { animated } = useAnimatedNumber(target);

    expect(animated.value).toBe(0);
  });

  it('animates toward new target value', async () => {
    const target = ref(0);
    const { animated } = useAnimatedNumber(target, 600);

    target.value = 100;
    await nextTick();

    // Mid-animation
    flushRaf(300);
    expect(animated.value).toBeGreaterThan(0);
    expect(animated.value).toBeLessThan(100);

    // Complete animation
    flushRaf(600);
    expect(animated.value).toBe(100);
  });

  it('sets value immediately when target equals current', async () => {
    const target = ref(50);
    const { animated } = useAnimatedNumber(target);

    target.value = 50;
    await nextTick();

    expect(animated.value).toBe(50);
    expect(requestAnimationFrame).not.toHaveBeenCalled();
  });

  it('cancels previous animation when target changes mid-flight', async () => {
    const target = ref(0);
    const { animated } = useAnimatedNumber(target, 600);

    target.value = 100;
    await nextTick();
    flushRaf(200);

    const midValue = animated.value;
    expect(midValue).toBeGreaterThan(0);

    // Change target before animation completes
    target.value = 200;
    await nextTick();

    expect(cancelAnimationFrame).toHaveBeenCalled();

    // Complete new animation
    flushRaf(900);
    expect(animated.value).toBe(200);
  });

  it('skips animation when resolved from and to are equal', async () => {
    const target = ref(null);
    const { animated } = useAnimatedNumber(target, 600);
    expect(animated.value).toBe(0);

    target.value = 0;
    await nextTick();

    expect(animated.value).toBe(0);
    expect(requestAnimationFrame).not.toHaveBeenCalled();
  });

  it('handles target changing to null', async () => {
    const target = ref(100);
    const { animated } = useAnimatedNumber(target, 600);

    target.value = null;
    await nextTick();

    flushRaf(600);
    expect(animated.value).toBe(0);
  });

  it('uses animated value as from when oldVal is null', async () => {
    const target = ref(null);
    const { animated } = useAnimatedNumber(target, 600);

    expect(animated.value).toBe(0);

    target.value = 50;
    await nextTick();

    flushRaf(600);
    expect(animated.value).toBe(50);
  });
});

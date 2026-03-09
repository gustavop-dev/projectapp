import { ref, watch } from 'vue';

/**
 * Composable that smoothly animates a number from its previous value to a new target.
 * @param {import('vue').Ref<number>} target - Reactive ref with the target number
 * @param {number} duration - Animation duration in milliseconds (default 600)
 * @returns {{ animated: import('vue').Ref<number> }}
 */
export function useAnimatedNumber(target, duration = 600) {
  const animated = ref(target.value || 0);
  let rafId = null;

  watch(target, (newVal, oldVal) => {
    if (rafId) cancelAnimationFrame(rafId);

    const from = oldVal ?? animated.value ?? 0;
    const to = newVal ?? 0;
    if (from === to) {
      animated.value = to;
      return;
    }

    const startTime = performance.now();
    const diff = to - from;

    function step(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      animated.value = Math.round(from + diff * ease);

      if (progress < 1) {
        rafId = requestAnimationFrame(step);
      } else {
        animated.value = to;
        rafId = null;
      }
    }

    rafId = requestAnimationFrame(step);
  });

  return { animated };
}

import { computed } from 'vue';
import { usePreferredReducedMotion } from '@vueuse/core';

/**
 * Reactive `prefers-reduced-motion` flag for JS-driven animation.
 *
 * Rule of thumb for respecting reduced motion in this codebase:
 * - Pure CSS transitions/animations -> Tailwind `motion-safe:` /
 *   `motion-reduce:` variants (or a media query in scoped CSS).
 * - JS-driven motion (GSAP, rAF count-ups, ApexCharts options) -> this
 *   composable: skip the animation and jump to the final state instead.
 *
 * SSR-safe: resolves to `false` on the server and before hydration.
 *
 * @returns {{ reducedMotion: import('vue').ComputedRef<boolean> }}
 */
export function useReducedMotion() {
  const preference = usePreferredReducedMotion();
  const reducedMotion = computed(() => preference.value === 'reduce');
  return { reducedMotion };
}

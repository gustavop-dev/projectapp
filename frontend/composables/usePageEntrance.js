import { onMounted, nextTick } from 'vue';
import { gsap } from 'gsap';

/**
 * Composable for staggered page entrance animations.
 * 
 * Add `data-enter` attribute to elements you want to animate on page load.
 * Optionally add `data-enter-delay="0.1"` for custom per-element delay.
 * Elements animate in order of appearance with a smooth fade-up stagger.
 *
 * Usage in any page:
 *   usePageEntrance()
 *   // then in template: <h1 data-enter>Title</h1> <p data-enter>Subtitle</p>
 */
export function usePageEntrance(containerSelector = null) {
  onMounted(() => {
    nextTick(() => {
      // Small delay to let the page transition finish first
      setTimeout(() => {
        const container = containerSelector
          ? document.querySelector(containerSelector)
          : document.body;
        if (!container) return;

        const elements = container.querySelectorAll('[data-enter]');
        if (!elements.length) return;

        // Set initial state
        gsap.set(elements, { opacity: 0, y: 20 });

        // Stagger animate in
        gsap.to(elements, {
          opacity: 1,
          y: 0,
          duration: 0.6,
          stagger: 0.08,
          ease: 'power2.out',
        });
      }, 50);
    });
  });
}

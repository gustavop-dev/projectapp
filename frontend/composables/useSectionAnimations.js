import { onMounted, onBeforeUnmount, inject, watch, ref } from 'vue';

/**
 * Composable for adding entrance animations to proposal sections.
 *
 * Queries child elements with [data-animate] attribute and creates
 * GSAP entrance animations triggered by the horizontal ScrollTrigger.
 *
 * Supported data-animate values:
 * - "fade-up": fade in + slide up
 * - "fade-up-stagger": fade in + slide up with stagger (applied to children)
 * - "scale-in": scale from 0.9 to 1 + fade
 *
 * @param {import('vue').Ref} sectionRef - Ref to the section root element
 */
export function useSectionAnimations(sectionRef) {
  const horizontalTweenRef = inject('horizontalTweenRef', ref(null));
  let timeline = null;
  let triggers = [];

  async function initAnimations(containerTween) {
    cleanup();

    if (!sectionRef.value || !containerTween) return;

    const { gsap } = await import('gsap');
    const { ScrollTrigger } = await import('gsap/ScrollTrigger');
    gsap.registerPlugin(ScrollTrigger);

    const section = sectionRef.value;

    // Collect all [data-animate] elements
    const fadeUpEls = section.querySelectorAll('[data-animate="fade-up"]');
    const staggerEls = section.querySelectorAll('[data-animate="fade-up-stagger"]');
    const scaleEls = section.querySelectorAll('[data-animate="scale-in"]');

    // Set initial states
    if (fadeUpEls.length) gsap.set(fadeUpEls, { opacity: 0, y: 24 });
    if (scaleEls.length) gsap.set(scaleEls, { opacity: 0, scale: 0.92 });

    staggerEls.forEach((container) => {
      const children = container.children;
      if (children.length) gsap.set(children, { opacity: 0, y: 18 });
    });

    // Create timeline with ScrollTrigger on the section
    timeline = gsap.timeline({
      defaults: { ease: 'power3.out' },
      scrollTrigger: {
        trigger: section,
        containerAnimation: containerTween,
        start: 'left 75%',
        toggleActions: 'play none none reverse',
      },
    });

    // Animate fade-up elements
    if (fadeUpEls.length) {
      timeline.to(fadeUpEls, {
        opacity: 1,
        y: 0,
        duration: 0.7,
        stagger: 0.1,
      }, 0);
    }

    // Animate stagger containers (children stagger)
    staggerEls.forEach((container) => {
      const children = container.children;
      if (children.length) {
        timeline.to(children, {
          opacity: 1,
          y: 0,
          duration: 0.5,
          stagger: 0.06,
        }, 0.2);
      }
    });

    // Animate scale-in elements
    if (scaleEls.length) {
      timeline.to(scaleEls, {
        opacity: 1,
        scale: 1,
        duration: 0.6,
        stagger: 0.08,
      }, 0.15);
    }
  }

  function cleanup() {
    if (timeline) {
      timeline.scrollTrigger?.kill();
      timeline.kill();
      timeline = null;
    }
    triggers.forEach((t) => t.kill());
    triggers = [];
  }

  watch(
    () => horizontalTweenRef.value,
    (tween) => {
      if (tween) initAnimations(tween);
    },
    { immediate: true },
  );

  onBeforeUnmount(cleanup);
}

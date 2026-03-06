import { onMounted, onBeforeUnmount, inject, watch, ref } from 'vue';

/**
 * Composable for adding entrance animations to proposal sections.
 *
 * Queries child elements with [data-animate] attribute, sorts them by
 * vertical position (top-to-bottom), and animates them in sequence with
 * a uniform fade-up effect. Creates a fluid waterfall cascade.
 *
 * Supported data-animate values:
 * - "fade-up": element participates in the top-to-bottom cascade
 * - "fade-up-stagger": each direct child participates individually
 *
 * @param {import('vue').Ref} sectionRef - Ref to the section root element
 */
export function useSectionAnimations(sectionRef) {
  const horizontalTweenRef = inject('horizontalTweenRef', ref(null));
  let timeline = null;
  let triggers = [];
  let mountTimer = null;

  async function buildTimeline(section, gsap, scrollTriggerOpts) {
    // Collect ALL [data-animate] elements and their stagger-children
    const directEls = Array.from(section.querySelectorAll('[data-animate]'));
    const animTargets = [];

    for (const el of directEls) {
      const type = el.getAttribute('data-animate');
      if (type === 'fade-up-stagger') {
        // For stagger containers, animate each child individually
        const children = Array.from(el.children);
        if (children.length) {
          children.forEach((child) => animTargets.push(child));
        }
      } else {
        animTargets.push(el);
      }
    }

    // Sort by vertical position (top-to-bottom cascade)
    animTargets.sort((a, b) => {
      const aRect = a.getBoundingClientRect();
      const bRect = b.getBoundingClientRect();
      return aRect.top - bRect.top || aRect.left - bRect.left;
    });

    if (!animTargets.length) return;

    // Set initial state: all hidden + slight slide up
    gsap.set(animTargets, { opacity: 0, y: 20 });

    // Create timeline (with or without ScrollTrigger)
    const timelineOpts = { defaults: { ease: 'power3.out' } };
    if (scrollTriggerOpts) {
      timelineOpts.scrollTrigger = scrollTriggerOpts;
    }
    timeline = gsap.timeline(timelineOpts);

    // Single sequential animation: fade-up each element in DOM-vertical order
    timeline.to(animTargets, {
      opacity: 1,
      y: 0,
      duration: 1.4,
      stagger: 0.25,
    }, 0);
  }

  async function initWithScrollTrigger(containerTween) {
    cleanup();
    if (!sectionRef.value || !containerTween) return;

    const { gsap } = await import('gsap');
    const { ScrollTrigger } = await import('gsap/ScrollTrigger');
    gsap.registerPlugin(ScrollTrigger);

    await buildTimeline(sectionRef.value, gsap, {
      trigger: sectionRef.value,
      containerAnimation: containerTween,
      start: 'left 75%',
      toggleActions: 'play none none reverse',
    });
  }

  async function initOnMount() {
    cleanup();
    if (!sectionRef.value) return;

    const { gsap } = await import('gsap');

    // Short delay so Vue transition finishes before animations start
    await buildTimeline(sectionRef.value, gsap, null);
  }

  function cleanup() {
    if (mountTimer) { clearTimeout(mountTimer); mountTimer = null; }
    if (timeline) {
      timeline.scrollTrigger?.kill();
      timeline.kill();
      timeline = null;
    }
    triggers.forEach((t) => t.kill());
    triggers = [];
  }

  // If a horizontal tween is provided (legacy mode), use ScrollTrigger
  watch(
    () => horizontalTweenRef.value,
    (tween) => {
      if (tween) initWithScrollTrigger(tween);
    },
    { immediate: true },
  );

  // Mount-based animations: if no horizontal tween after a short delay, animate on mount
  onMounted(() => {
    mountTimer = setTimeout(() => {
      mountTimer = null;
      if (!horizontalTweenRef.value && !timeline) {
        initOnMount();
      }
    }, 50);
  });

  onBeforeUnmount(cleanup);
}

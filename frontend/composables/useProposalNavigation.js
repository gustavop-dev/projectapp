import { ref, computed } from 'vue';

/**
 * Composable for tracking and navigating between proposal sections
 * in the horizontal scroll view.
 *
 * @param {import('vue').Ref<Array>} sections - Enabled sections array
 * @returns {object} Navigation state and methods
 */
export function useProposalNavigation(sections) {
  const currentIndex = ref(0);

  const totalSections = computed(() => sections.value?.length || 0);

  const progress = computed(() =>
    totalSections.value > 0
      ? (currentIndex.value + 1) / totalSections.value
      : 0,
  );

  /**
   * Called by GSAP ScrollTrigger to sync the active panel index.
   * @param {number} index - Currently visible panel index.
   */
  function onScrollUpdate(index) {
    if (index >= 0 && index < totalSections.value) {
      currentIndex.value = index;
    }
  }

  /**
   * Programmatically scroll to a specific section by index.
   * Requires a ref to the GSAP horizontal tween and panels array.
   *
   * @param {number} index - Target panel index.
   * @param {object} [opts] - Optional { tween, panels, scrollContainer }.
   */
  async function goToSection(index, opts = {}) {
    if (index < 0 || index >= totalSections.value) return;

    const { tween, panels, scrollContainer } = opts;

    if (tween && panels && scrollContainer) {
      const panelEls = panels.value || panels;
      if (!panelEls[index]) return;

      const containerEl = scrollContainer.value || scrollContainer;
      const panelLeft = panelEls[index].offsetLeft;
      const totalScroll = containerEl.scrollWidth - containerEl.offsetWidth;
      const targetProgress = totalScroll > 0 ? panelLeft / totalScroll : 0;

      const { gsap } = await import('gsap');
      const scrollTrigger = tween.scrollTrigger;
      if (scrollTrigger) {
        gsap.to(window, {
          scrollTo: {
            y: scrollTrigger.start + (scrollTrigger.end - scrollTrigger.start) * targetProgress,
          },
          duration: 0.8,
          ease: 'power2.inOut',
        });
      }
    }

    currentIndex.value = index;
  }

  /**
   * Navigate to the next section.
   */
  function goNext(opts = {}) {
    goToSection(currentIndex.value + 1, opts);
  }

  /**
   * Navigate to the previous section.
   */
  function goPrev(opts = {}) {
    goToSection(currentIndex.value - 1, opts);
  }

  return {
    currentIndex,
    totalSections,
    progress,
    goToSection,
    goNext,
    goPrev,
    onScrollUpdate,
  };
}

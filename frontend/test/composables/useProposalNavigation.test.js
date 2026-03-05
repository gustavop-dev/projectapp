/**
 * Tests for the useProposalNavigation composable.
 *
 * Covers: currentIndex, totalSections, progress, onScrollUpdate,
 * goToSection, goNext, goPrev with various section states.
 */
import { ref } from 'vue';
import { useProposalNavigation } from '../../composables/useProposalNavigation';

describe('useProposalNavigation', () => {
  const makeSections = (count) => ref(Array.from({ length: count }, (_, i) => ({ id: i })));

  describe('initial state', () => {
    it('starts at index 0', () => {
      const { currentIndex } = useProposalNavigation(makeSections(5));

      expect(currentIndex.value).toBe(0);
    });

    it('computes totalSections from sections ref', () => {
      const { totalSections } = useProposalNavigation(makeSections(3));

      expect(totalSections.value).toBe(3);
    });

    it('returns 0 totalSections for empty array', () => {
      const { totalSections } = useProposalNavigation(ref([]));

      expect(totalSections.value).toBe(0);
    });

    it('returns 0 totalSections for null sections', () => {
      const { totalSections } = useProposalNavigation(ref(null));

      expect(totalSections.value).toBe(0);
    });
  });

  describe('progress', () => {
    it('returns initial progress as 1/total', () => {
      const { progress } = useProposalNavigation(makeSections(4));

      expect(progress.value).toBe(0.25);
    });

    it('returns 0 when no sections', () => {
      const { progress } = useProposalNavigation(ref([]));

      expect(progress.value).toBe(0);
    });

    it('updates progress after scroll', () => {
      const { progress, onScrollUpdate } = useProposalNavigation(makeSections(4));

      onScrollUpdate(3);

      expect(progress.value).toBe(1);
    });
  });

  describe('onScrollUpdate', () => {
    it('updates currentIndex to valid index', () => {
      const { currentIndex, onScrollUpdate } = useProposalNavigation(makeSections(5));

      onScrollUpdate(2);

      expect(currentIndex.value).toBe(2);
    });

    it('ignores negative index', () => {
      const { currentIndex, onScrollUpdate } = useProposalNavigation(makeSections(5));

      onScrollUpdate(-1);

      expect(currentIndex.value).toBe(0);
    });

    it('ignores index beyond total sections', () => {
      const { currentIndex, onScrollUpdate } = useProposalNavigation(makeSections(3));

      onScrollUpdate(5);

      expect(currentIndex.value).toBe(0);
    });
  });

  describe('goToSection', () => {
    it('updates currentIndex when no opts provided', async () => {
      const { currentIndex, goToSection } = useProposalNavigation(makeSections(5));

      await goToSection(3);

      expect(currentIndex.value).toBe(3);
    });

    it('does nothing for negative index', async () => {
      const { currentIndex, goToSection } = useProposalNavigation(makeSections(5));

      await goToSection(-1);

      expect(currentIndex.value).toBe(0);
    });

    it('does nothing for index beyond total', async () => {
      const { currentIndex, goToSection } = useProposalNavigation(makeSections(3));

      await goToSection(10);

      expect(currentIndex.value).toBe(0);
    });

    it('scrolls via GSAP when tween, panels, and scrollContainer provided', async () => {
      const mockGsapTo = jest.fn();
      jest.doMock('gsap', () => ({
        gsap: { to: mockGsapTo },
      }));

      const panels = ref([
        { offsetLeft: 0 },
        { offsetLeft: 500 },
        { offsetLeft: 1000 },
      ]);
      const scrollContainer = ref({
        scrollWidth: 1500,
        offsetWidth: 500,
      });
      const tween = {
        scrollTrigger: { start: 0, end: 1000 },
      };

      const { currentIndex, goToSection } = useProposalNavigation(makeSections(3));

      await goToSection(1, { tween, panels, scrollContainer });

      expect(currentIndex.value).toBe(1);
    });

    it('returns early when panel element does not exist', async () => {
      const panels = ref([{ offsetLeft: 0 }, null]);
      const scrollContainer = ref({ scrollWidth: 1000, offsetWidth: 500 });
      const tween = { scrollTrigger: { start: 0, end: 1000 } };

      const { currentIndex, goToSection } = useProposalNavigation(makeSections(3));

      await goToSection(1, { tween, panels, scrollContainer });

      expect(currentIndex.value).toBe(0);
    });
  });

  describe('goNext', () => {
    it('advances to next section', async () => {
      const { currentIndex, goNext } = useProposalNavigation(makeSections(3));

      await goNext();

      expect(currentIndex.value).toBe(1);
    });

    it('does not advance past last section', async () => {
      const { currentIndex, goNext, onScrollUpdate } = useProposalNavigation(makeSections(3));
      onScrollUpdate(2);

      await goNext();

      expect(currentIndex.value).toBe(2);
    });
  });

  describe('goPrev', () => {
    it('goes to previous section', async () => {
      const { currentIndex, goPrev, onScrollUpdate } = useProposalNavigation(makeSections(3));
      onScrollUpdate(2);

      await goPrev();

      expect(currentIndex.value).toBe(1);
    });

    it('does not go before first section', async () => {
      const { currentIndex, goPrev } = useProposalNavigation(makeSections(3));

      await goPrev();

      expect(currentIndex.value).toBe(0);
    });
  });
});

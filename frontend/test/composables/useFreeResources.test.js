/**
 * Tests for the useFreeResources composable.
 *
 * Covers: modalRefs initialization, freeMediaResources (video/image cleanup),
 * closeModals, watch behavior.
 */
import { ref } from 'vue';
import { useFreeResources } from '../../composables/useFreeResources';

describe('useFreeResources', () => {
  describe('default initialization', () => {
    it('returns empty modalRefs when no modals provided', () => {
      const { modalRefs } = useFreeResources();

      expect(modalRefs).toEqual([]);
    });

    it('returns functions for closeModals and freeMediaResources', () => {
      const { closeModals, freeMediaResources } = useFreeResources();

      expect(typeof closeModals).toBe('function');
      expect(typeof freeMediaResources).toBe('function');
    });
  });

  describe('modalRefs', () => {
    it('creates one ref per modal', () => {
      const { modalRefs } = useFreeResources({ modals: ['modal1', 'modal2'] });

      expect(modalRefs).toHaveLength(2);
      expect(modalRefs[0].value).toBe(false);
      expect(modalRefs[1].value).toBe(false);
    });
  });

  describe('closeModals', () => {
    it('sets all modalRefs to false', () => {
      const { modalRefs, closeModals } = useFreeResources({ modals: ['a', 'b'] });
      modalRefs[0].value = true;
      modalRefs[1].value = true;

      closeModals();

      expect(modalRefs[0].value).toBe(false);
      expect(modalRefs[1].value).toBe(false);
    });
  });

  describe('watch behavior', () => {
    it('closes modals when a modal ref becomes true', async () => {
      const { nextTick } = require('vue');
      const { modalRefs } = useFreeResources({ modals: ['a', 'b'] });

      modalRefs[0].value = true;
      await nextTick();

      expect(modalRefs[0].value).toBe(false);
      expect(modalRefs[1].value).toBe(false);
    });
  });

  describe('freeMediaResources', () => {
    it('clears video src and calls load', () => {
      const mockVideo = ref({ src: 'video.mp4', load: jest.fn() });
      const { freeMediaResources } = useFreeResources({ videos: [mockVideo] });

      freeMediaResources();

      expect(mockVideo.value.src).toBe('');
      expect(mockVideo.value.load).toHaveBeenCalled();
    });

    it('clears image src', () => {
      const mockImage = ref({ src: 'image.jpg' });
      const { freeMediaResources } = useFreeResources({ images: [mockImage] });

      freeMediaResources();

      expect(mockImage.value.src).toBe('');
    });

    it('skips null video refs', () => {
      const mockVideo = ref(null);
      const { freeMediaResources } = useFreeResources({ videos: [mockVideo] });

      expect(() => freeMediaResources()).not.toThrow();
    });

    it('skips null image refs', () => {
      const mockImage = ref(null);
      const { freeMediaResources } = useFreeResources({ images: [mockImage] });

      expect(() => freeMediaResources()).not.toThrow();
    });

    it('handles multiple videos and images', () => {
      const video1 = ref({ src: 'a.mp4', load: jest.fn() });
      const video2 = ref({ src: 'b.mp4', load: jest.fn() });
      const img1 = ref({ src: 'a.jpg' });
      const { freeMediaResources } = useFreeResources({
        videos: [video1, video2],
        images: [img1],
      });

      freeMediaResources();

      expect(video1.value.src).toBe('');
      expect(video2.value.src).toBe('');
      expect(img1.value.src).toBe('');
    });
  });
});

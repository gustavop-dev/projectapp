/**
 * Tests for the web_designs store.
 *
 * Covers: init, fetchDesignsData, getFilteredDesignsAndCategories getter.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useWebDesignsStore } from '../../stores/web_designs';
import { useLanguageStore } from '../../stores/language';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const mockDesign = {
  title_en: 'Modern Dashboard',
  title_es: 'Dashboard Moderno',
  cover_image: '/img/dash.jpg',
  detail_image: '/img/dash-detail.jpg',
  category_title_en: 'Web Design',
  category_title_es: 'Diseño Web',
};

describe('useWebDesignsStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useWebDesignsStore();
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('has empty designs array', () => {
      expect(store.designs).toEqual([]);
    });

    it('has areUpdateDesigns false', () => {
      expect(store.areUpdateDesigns).toBe(false);
    });
  });

  describe('fetchDesignsData', () => {
    it('fetches designs and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockDesign] });

      await store.fetchDesignsData();

      expect(get_request).toHaveBeenCalledWith('designs/');
      expect(store.designs).toHaveLength(1);
      expect(store.areUpdateDesigns).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areUpdateDesigns = true;

      await store.fetchDesignsData();

      expect(get_request).not.toHaveBeenCalled();
    });

  });

  describe('init', () => {
    it('calls fetch when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areUpdateDesigns = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('getFilteredDesignsAndCategories getter', () => {
    it('returns English fields when language is en', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.designs = [mockDesign];

      const result = store.getFilteredDesignsAndCategories;

      expect(result.designs[0].title).toBe('Modern Dashboard');
      expect(result.designs[0].category_title).toBe('Web Design');
    });

    it('returns Spanish fields when language is es', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'es';
      store.designs = [mockDesign];

      const result = store.getFilteredDesignsAndCategories;

      expect(result.designs[0].title).toBe('Dashboard Moderno');
    });

    it('returns unique categories', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.designs = [mockDesign, { ...mockDesign, title_en: 'Other' }];

      const result = store.getFilteredDesignsAndCategories;

      expect(result.categories).toHaveLength(1);
    });
  });
});

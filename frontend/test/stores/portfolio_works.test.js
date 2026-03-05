/**
 * Tests for the portfolio_works store.
 *
 * Covers: init, fetchPortfolioWorksData, getFilteredPortfolioWorksAndCategories getter.
 */
import { setActivePinia, createPinia } from 'pinia';
import { usePortfolioWorksStore } from '../../stores/portfolio_works';
import { useLanguageStore } from '../../stores/language';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const mockWork = {
  title_en: 'Client Portal',
  title_es: 'Portal de Cliente',
  cover_image: '/img/portal.jpg',
  project_url: 'https://example.com',
  category_title_en: 'Web App',
  category_title_es: 'Aplicación Web',
};

describe('usePortfolioWorksStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = usePortfolioWorksStore();
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('has empty portfolioWorks array', () => {
      expect(store.portfolioWorks).toEqual([]);
    });

    it('has areUpdatePortfolioWorks false', () => {
      expect(store.areUpdatePortfolioWorks).toBe(false);
    });
  });

  describe('fetchPortfolioWorksData', () => {
    it('fetches works and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockWork] });

      await store.fetchPortfolioWorksData();

      expect(get_request).toHaveBeenCalledWith('portfolio_works/');
      expect(store.portfolioWorks).toHaveLength(1);
      expect(store.areUpdatePortfolioWorks).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areUpdatePortfolioWorks = true;

      await store.fetchPortfolioWorksData();

      expect(get_request).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      await store.fetchPortfolioWorksData();

      expect(store.portfolioWorks).toEqual([]);
    });

    it('handles string JSON response', async () => {
      get_request.mockResolvedValue({ data: JSON.stringify([mockWork]) });

      await store.fetchPortfolioWorksData();

      expect(store.portfolioWorks).toHaveLength(1);
    });

    it('handles invalid JSON string by falling back to empty array', async () => {
      get_request.mockResolvedValue({ data: '{bad json' });

      await store.fetchPortfolioWorksData();

      expect(store.portfolioWorks).toEqual([]);
      expect(store.areUpdatePortfolioWorks).toBe(true);
    });
  });

  describe('init', () => {
    it('calls fetch when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areUpdatePortfolioWorks = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('getFilteredPortfolioWorksAndCategories getter', () => {
    it('returns English fields when language is en', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.portfolioWorks = [mockWork];

      const result = store.getFilteredPortfolioWorksAndCategories;

      expect(result.portfolioWorks[0].title).toBe('Client Portal');
      expect(result.portfolioWorks[0].category_title).toBe('Web App');
    });

    it('returns Spanish fields when language is es', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'es';
      store.portfolioWorks = [mockWork];

      const result = store.getFilteredPortfolioWorksAndCategories;

      expect(result.portfolioWorks[0].title).toBe('Portal de Cliente');
    });

    it('returns unique categories', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.portfolioWorks = [mockWork, { ...mockWork, title_en: 'Another' }];

      const result = store.getFilteredPortfolioWorksAndCategories;

      expect(result.categories).toHaveLength(1);
      expect(result.categories[0]).toBe('Web App');
    });

    it('returns empty when no works', () => {
      const result = store.getFilteredPortfolioWorksAndCategories;

      expect(result.portfolioWorks).toEqual([]);
      expect(result.categories).toEqual([]);
    });
  });

  describe('getFilteredByCategory getter', () => {
    it('returns all works when category is All', () => {
      const works = [{ category_title: 'A' }, { category_title: 'B' }];

      const result = store.getFilteredByCategory(works, 'All');

      expect(result).toHaveLength(2);
    });

    it('filters works by selected category', () => {
      const works = [
        { category_title: 'Web App' },
        { category_title: 'Mobile' },
      ];

      const result = store.getFilteredByCategory(works, 'Web App');

      expect(result).toHaveLength(1);
      expect(result[0].category_title).toBe('Web App');
    });
  });
});

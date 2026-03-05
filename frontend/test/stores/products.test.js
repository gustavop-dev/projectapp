/**
 * Tests for the products store.
 *
 * Covers: init, fetchProductData, getProducts getter with language filtering.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useProductStore } from '../../stores/products';
import { useLanguageStore } from '../../stores/language';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const mockProduct = {
  id: 1,
  title_en: 'E-Commerce Platform',
  title_es: 'Plataforma E-Commerce',
  description_en: 'Full solution.',
  description_es: 'Solución completa.',
  price: '4999.99',
  mobile_app_price: '2999.99',
  development_time_en: '8-12 weeks',
  development_time_es: '8-12 semanas',
  categories: [],
  image: '/img/product.jpg',
};

describe('useProductStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useProductStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  describe('initial state', () => {
    it('has empty products array', () => {
      expect(store.products).toEqual([]);
    });

    it('has areProductsUpdated false', () => {
      expect(store.areProductsUpdated).toBe(false);
    });
  });

  describe('fetchProductData', () => {
    it('fetches products and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockProduct] });

      await store.fetchProductData();

      expect(get_request).toHaveBeenCalledWith('products/');
      expect(store.products).toHaveLength(1);
      expect(store.areProductsUpdated).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areProductsUpdated = true;

      await store.fetchProductData();

      expect(get_request).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      get_request.mockRejectedValue(new Error('Network error'));

      await store.fetchProductData();

      expect(store.products).toEqual([]);
    });

    it('handles string JSON response', async () => {
      get_request.mockResolvedValue({ data: JSON.stringify([mockProduct]) });

      await store.fetchProductData();

      expect(store.products).toHaveLength(1);
    });

    it('handles invalid JSON string by falling back to empty array', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      get_request.mockResolvedValue({ data: '{bad json' });

      await store.fetchProductData();

      expect(store.products).toEqual([]);
      expect(store.areProductsUpdated).toBe(true);
    });

    it('falls back to empty array when response data is null', async () => {
      get_request.mockResolvedValue({ data: null });

      await store.fetchProductData();

      expect(store.products).toEqual([]);
      expect(store.areProductsUpdated).toBe(true);
    });
  });

  describe('init', () => {
    it('calls fetch when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areProductsUpdated = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('getProducts getter', () => {
    it('returns English fields when language is en', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.products = [mockProduct];

      const result = store.getProducts;

      expect(result[0].title).toBe('E-Commerce Platform');
      expect(result[0].description).toBe('Full solution.');
      expect(result[0].development_time).toBe('8-12 weeks');
    });

    it('returns Spanish fields when language is es', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'es';
      store.products = [mockProduct];

      const result = store.getProducts;

      expect(result[0].title).toBe('Plataforma E-Commerce');
      expect(result[0].description).toBe('Solución completa.');
    });

    it('returns empty array when no products', () => {
      expect(store.getProducts).toEqual([]);
    });

    it('handles null mobile_app_price', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.products = [{ ...mockProduct, mobile_app_price: null }];

      const result = store.getProducts;

      expect(result[0].mobile_app_price).toBeNull();
    });

    it('filters nested category and item objects by language', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      const productWithCategories = {
        ...mockProduct,
        categories: [
          {
            title_en: 'Features',
            title_es: 'Características',
            items: [
              { name_en: 'SEO', name_es: 'SEO' },
            ],
          },
        ],
      };
      store.products = [productWithCategories];

      const result = store.getProducts;

      expect(result[0].categories[0].title).toBe('Features');
      expect(result[0].categories[0].items[0].name).toBe('SEO');
    });
  });
});

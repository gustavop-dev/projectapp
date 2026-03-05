/**
 * Tests for the models_3d store.
 *
 * Covers: init, fetchModels3dData, getFilteredModelsAndCategories getter.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useModels3dStore } from '../../stores/models_3d';
import { useLanguageStore } from '../../stores/language';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const mockModel = {
  title_en: 'Product Viewer',
  title_es: 'Visor de Producto',
  image: '/img/3d.jpg',
  file: '/models/viewer.glb',
  category_title_en: '3D Animation',
  category_title_es: 'Animación 3D',
};

describe('useModels3dStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useModels3dStore();
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('has empty models3d array', () => {
      expect(store.models3d).toEqual([]);
    });

    it('has areUpdateModels3d false', () => {
      expect(store.areUpdateModels3d).toBe(false);
    });
  });

  describe('fetchModels3dData', () => {
    it('fetches models and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockModel] });

      await store.fetchModels3dData();

      expect(get_request).toHaveBeenCalledWith('models3d/');
      expect(store.models3d).toHaveLength(1);
      expect(store.areUpdateModels3d).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areUpdateModels3d = true;

      await store.fetchModels3dData();

      expect(get_request).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      await store.fetchModels3dData();

      expect(store.models3d).toEqual([]);
    });

    it('handles string JSON response', async () => {
      get_request.mockResolvedValue({ data: JSON.stringify([mockModel]) });

      await store.fetchModels3dData();

      expect(store.models3d).toHaveLength(1);
    });

    it('handles invalid JSON string by falling back to empty array', async () => {
      get_request.mockResolvedValue({ data: '{bad json' });

      await store.fetchModels3dData();

      expect(store.models3d).toEqual([]);
      expect(store.areUpdateModels3d).toBe(true);
    });
  });

  describe('init', () => {
    it('calls fetch when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areUpdateModels3d = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('getFilteredModelsAndCategories getter', () => {
    it('returns English fields when language is en', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.models3d = [mockModel];

      const result = store.getFilteredModelsAndCategories;

      expect(result.models[0].title).toBe('Product Viewer');
      expect(result.models[0].category_title).toBe('3D Animation');
    });

    it('returns Spanish fields when language is es', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'es';
      store.models3d = [mockModel];

      const result = store.getFilteredModelsAndCategories;

      expect(result.models[0].title).toBe('Visor de Producto');
    });

    it('returns unique categories', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.models3d = [mockModel, { ...mockModel, title_en: 'Other' }];

      const result = store.getFilteredModelsAndCategories;

      expect(result.categories).toHaveLength(1);
      expect(result.categories[0]).toBe('3D Animation');
    });
  });

  describe('getFilteredByCategory getter', () => {
    it('returns all models when category is All', () => {
      const models = [{ category_title: 'A' }, { category_title: 'B' }];

      const result = store.getFilteredByCategory(models, 'All');

      expect(result).toHaveLength(2);
    });

    it('filters models by selected category', () => {
      const models = [
        { category_title: '3D Animation' },
        { category_title: 'Product' },
      ];

      const result = store.getFilteredByCategory(models, '3D Animation');

      expect(result).toHaveLength(1);
      expect(result[0].category_title).toBe('3D Animation');
    });
  });
});

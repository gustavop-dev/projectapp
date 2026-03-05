/**
 * Tests for the hosting store.
 *
 * Covers: init, fetchHostingData, getHostings getter with language filtering.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useHostingStore } from '../../stores/hosting';
import { useLanguageStore } from '../../stores/language';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

const mockHosting = {
  title_en: 'Professional Plan',
  title_es: 'Plan Profesional',
  description_en: 'Best for growing businesses.',
  description_es: 'Ideal para negocios en crecimiento.',
  cpu_cores_en: '4 vCPUs',
  cpu_cores_es: '4 vCPUs',
  ram_en: '8 GB',
  ram_es: '8 GB',
  storage_en: '100 GB SSD',
  storage_es: '100 GB SSD',
  bandwidth_en: 'Unlimited',
  bandwidth_es: 'Ilimitado',
  data_center_location_en: 'US East',
  data_center_location_es: 'Este de EE.UU.',
  operating_system_en: 'Ubuntu 22.04',
  operating_system_es: 'Ubuntu 22.04',
  semi_annually_price: '149.99',
  annual_price: '249.99',
};

describe('useHostingStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useHostingStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  describe('initial state', () => {
    it('has empty hostings array', () => {
      expect(store.hostings).toEqual([]);
    });

    it('has areHostingsUpdated false', () => {
      expect(store.areHostingsUpdated).toBe(false);
    });
  });

  describe('fetchHostingData', () => {
    it('fetches hostings and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockHosting] });

      await store.fetchHostingData();

      expect(get_request).toHaveBeenCalledWith('hostings/');
      expect(store.hostings).toHaveLength(1);
      expect(store.areHostingsUpdated).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areHostingsUpdated = true;

      await store.fetchHostingData();

      expect(get_request).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      jest.spyOn(console, 'error').mockImplementation(() => {});
      get_request.mockRejectedValue(new Error('Network error'));

      await store.fetchHostingData();

      expect(store.hostings).toEqual([]);
    });

    it('handles string JSON response', async () => {
      get_request.mockResolvedValue({ data: JSON.stringify([mockHosting]) });

      await store.fetchHostingData();

      expect(store.hostings).toHaveLength(1);
    });
  });

  describe('init', () => {
    it('calls fetchHostingData when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areHostingsUpdated = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('getHostings getter', () => {
    it('returns English fields when language is en', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.hostings = [mockHosting];

      const result = store.getHostings;

      expect(result[0].title).toBe('Professional Plan');
      expect(result[0].description).toBe('Best for growing businesses.');
      expect(result[0].bandwidth).toBe('Unlimited');
    });

    it('returns Spanish fields when language is es', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'es';
      store.hostings = [mockHosting];

      const result = store.getHostings;

      expect(result[0].title).toBe('Plan Profesional');
      expect(result[0].description).toBe('Ideal para negocios en crecimiento.');
      expect(result[0].bandwidth).toBe('Ilimitado');
    });

    it('includes non-translated fields', () => {
      const langStore = useLanguageStore();
      langStore.currentLanguage = 'en';
      store.hostings = [mockHosting];

      const result = store.getHostings;

      expect(result[0].semi_annually_price).toBe('149.99');
      expect(result[0].annual_price).toBe('249.99');
    });

    it('returns empty array when no hostings', () => {
      expect(store.getHostings).toEqual([]);
    });
  });
});

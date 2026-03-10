/**
 * Tests for the portfolio_works store.
 *
 * Covers: initial state, fetchWorks, fetchWork, fetchAdminWorks,
 * createWork, updateWork, deleteWork, duplicateWork, getWorkById getter.
 */
import { setActivePinia, createPinia } from 'pinia';
import { usePortfolioWorksStore } from '../../stores/portfolio_works';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

const mockWork = {
  id: 1,
  title_es: 'Portal de Cliente',
  title_en: 'Client Portal',
  slug: 'client-portal',
  project_url: 'https://example.com',
};

describe('usePortfolioWorksStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = usePortfolioWorksStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has empty works array', () => {
      expect(store.works).toEqual([]);
    });

    it('has null currentWork', () => {
      expect(store.currentWork).toBeNull();
    });

    it('has isLoading false', () => {
      expect(store.isLoading).toBe(false);
    });

    it('has null error', () => {
      expect(store.error).toBeNull();
    });
  });

  describe('fetchWorks', () => {
    it('fetches public works and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockWork] });

      const result = await store.fetchWorks('es');

      expect(get_request).toHaveBeenCalledWith('portfolio/?lang=es');
      expect(store.works).toHaveLength(1);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchWorks();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });

    it('sets isLoading during fetch', async () => {
      get_request.mockResolvedValue({ data: [] });

      const promise = store.fetchWorks();
      expect(store.isLoading).toBe(true);
      await promise;
      expect(store.isLoading).toBe(false);
    });
  });

  describe('fetchWork', () => {
    it('fetches single work by slug', async () => {
      get_request.mockResolvedValue({ data: mockWork });

      const result = await store.fetchWork('client-portal', 'en');

      expect(get_request).toHaveBeenCalledWith('portfolio/client-portal/?lang=en');
      expect(store.currentWork).toEqual(mockWork);
      expect(result.success).toBe(true);
    });

    it('sets not_found error on 404', async () => {
      get_request.mockRejectedValue({ response: { status: 404 } });

      const result = await store.fetchWork('missing');

      expect(result.success).toBe(false);
      expect(store.error).toBe('not_found');
    });

    it('sets unknown error on other status', async () => {
      get_request.mockRejectedValue({ response: { status: 500 } });

      await store.fetchWork('error-slug');

      expect(store.error).toBe('unknown');
    });
  });

  describe('fetchAdminWorks', () => {
    it('fetches all admin works', async () => {
      get_request.mockResolvedValue({ data: [mockWork, { ...mockWork, id: 2 }] });

      const result = await store.fetchAdminWorks();

      expect(get_request).toHaveBeenCalledWith('portfolio/admin/');
      expect(store.works).toHaveLength(2);
      expect(result.success).toBe(true);
    });

    it('handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchAdminWorks();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('createWork', () => {
    it('creates work and returns data', async () => {
      create_request.mockResolvedValue({ data: mockWork });

      const result = await store.createWork({ title_es: 'New' });

      expect(create_request).toHaveBeenCalledWith('portfolio/admin/create/', { title_es: 'New' });
      expect(store.currentWork).toEqual(mockWork);
      expect(result.success).toBe(true);
    });

    it('handles validation error', async () => {
      create_request.mockRejectedValue({ response: { data: { title_es: ['required'] } } });

      const result = await store.createWork({});

      expect(result.success).toBe(false);
      expect(store.error).toBe('create_failed');
    });
  });

  describe('updateWork', () => {
    it('updates work and returns data', async () => {
      const updated = { ...mockWork, title_es: 'Updated' };
      patch_request.mockResolvedValue({ data: updated });

      const result = await store.updateWork(1, { title_es: 'Updated' });

      expect(patch_request).toHaveBeenCalledWith('portfolio/admin/1/update/', { title_es: 'Updated' });
      expect(store.currentWork).toEqual(updated);
      expect(result.success).toBe(true);
    });
  });

  describe('deleteWork', () => {
    it('deletes work and removes from list', async () => {
      store.works = [mockWork, { ...mockWork, id: 2 }];
      delete_request.mockResolvedValue({});

      const result = await store.deleteWork(1);

      expect(delete_request).toHaveBeenCalledWith('portfolio/admin/1/delete/');
      expect(store.works).toHaveLength(1);
      expect(store.works[0].id).toBe(2);
      expect(result.success).toBe(true);
    });

    it('clears currentWork if it matches deleted id', async () => {
      store.currentWork = mockWork;
      delete_request.mockResolvedValue({});

      await store.deleteWork(1);

      expect(store.currentWork).toBeNull();
    });

    it('handles delete error', async () => {
      delete_request.mockRejectedValue(new Error('fail'));

      const result = await store.deleteWork(99);

      expect(result.success).toBe(false);
      expect(store.error).toBe('delete_failed');
    });
  });

  describe('duplicateWork', () => {
    it('duplicates work and prepends to list', async () => {
      const dup = { ...mockWork, id: 3, title_es: 'Copy' };
      create_request.mockResolvedValue({ data: dup });
      store.works = [mockWork];

      const result = await store.duplicateWork(1);

      expect(store.works[0].id).toBe(3);
      expect(result.success).toBe(true);
    });

    it('handles duplicate error', async () => {
      create_request.mockRejectedValue(new Error('fail'));

      const result = await store.duplicateWork(99);

      expect(result.success).toBe(false);
      expect(store.error).toBe('duplicate_failed');
    });
  });

  describe('getWorkById getter', () => {
    it('finds work by id', () => {
      store.works = [mockWork, { ...mockWork, id: 2 }];

      expect(store.getWorkById(1)).toEqual(mockWork);
    });

    it('returns undefined for unknown id', () => {
      store.works = [mockWork];

      expect(store.getWorkById(999)).toBeUndefined();
    });
  });
});

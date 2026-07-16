/**
 * Tests for the view_map store.
 *
 * Covers: initial state, fetchSettings and updateSettings
 * (success and failure paths) against the panel settings singleton.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useViewMapStore } from '../../stores/view_map';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  patch_request: jest.fn(),
}));

const { get_request, patch_request } = require('../../stores/services/request_http');

const mockSettings = {
  default_view_mode: 'map',
  default_filters: { audiences: ['admin'] },
  updated_at: '2026-07-16T10:00:00Z',
};

describe('useViewMapStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useViewMapStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has null settings and is not updating', () => {
      expect(store.settings).toBeNull();
      expect(store.isUpdating).toBe(false);
    });
  });

  describe('fetchSettings', () => {
    it('loads the settings singleton', async () => {
      get_request.mockResolvedValue({ data: mockSettings });

      const result = await store.fetchSettings();

      expect(get_request).toHaveBeenCalledWith('view-map/admin/settings/');
      expect(result).toEqual({ success: true, data: mockSettings });
      expect(store.settings).toEqual(mockSettings);
    });

    it('returns failure and keeps settings null on error', async () => {
      get_request.mockRejectedValue(new Error('boom'));

      const result = await store.fetchSettings();

      expect(result.success).toBe(false);
      expect(store.settings).toBeNull();
    });
  });

  describe('updateSettings', () => {
    it('patches the singleton and stores the response', async () => {
      patch_request.mockResolvedValue({ data: mockSettings });

      const result = await store.updateSettings({ default_view_mode: 'map' });

      expect(patch_request).toHaveBeenCalledWith(
        'view-map/admin/settings/update/',
        { default_view_mode: 'map' },
      );
      expect(result.success).toBe(true);
      expect(store.settings).toEqual(mockSettings);
      expect(store.isUpdating).toBe(false);
    });

    it('returns backend errors on failure', async () => {
      const error = new Error('bad request');
      error.response = { data: { default_view_mode: ['inválido'] } };
      patch_request.mockRejectedValue(error);

      const result = await store.updateSettings({ default_view_mode: 'grid' });

      expect(result.success).toBe(false);
      expect(result.errors).toEqual({ default_view_mode: ['inválido'] });
      expect(store.settings).toBeNull();
      expect(store.isUpdating).toBe(false);
    });
  });
});

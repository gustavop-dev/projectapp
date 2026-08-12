/**
 * Tests for the linktrees store.
 * Covers: initial state, fetchLinktrees, fetchLinktree, fetchPublicLinktree,
 * createLinktree, updateLinktree, deleteLinktree.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useLinktreesStore } from '../../stores/linktrees';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

const mockLinktree = {
  id: '11111111-1111-1111-1111-111111111111',
  handle: 'gustavo',
  name: 'Gustavo',
  kind: 'personal',
  is_active: true,
  public_path: '/lk/@gustavo',
  buttons_count: 1,
};

describe('useLinktreesStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useLinktreesStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('starts empty, idle and error-free before any action runs', () => {
      expect(store.linktrees).toEqual([]);
      expect(store.currentLinktree).toBeNull();
      expect(store.publicLinktree).toBeNull();
      expect(store.isLoading).toBe(false);
      expect(store.error).toBeNull();
    });
  });

  describe('fetchLinktrees', () => {
    it('fetches linktrees and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockLinktree] });

      const result = await store.fetchLinktrees();

      expect(get_request).toHaveBeenCalledWith('linktrees/admin/');
      expect(store.linktrees).toHaveLength(1);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchLinktrees();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('fetchLinktree', () => {
    it('stores the detail as currentLinktree', async () => {
      get_request.mockResolvedValue({ data: { ...mockLinktree, buttons: [] } });

      const result = await store.fetchLinktree(mockLinktree.id);

      expect(get_request).toHaveBeenCalledWith(`linktrees/admin/${mockLinktree.id}/`);
      expect(store.currentLinktree.handle).toBe('gustavo');
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchLinktree(mockLinktree.id);

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('fetchPublicLinktree', () => {
    it('fetches by handle and stores publicLinktree', async () => {
      get_request.mockResolvedValue({ data: { handle: 'gustavo', buttons: [] } });

      const result = await store.fetchPublicLinktree('gustavo');

      expect(get_request).toHaveBeenCalledWith('linktrees/public/gustavo/');
      expect(store.publicLinktree.handle).toBe('gustavo');
      expect(result.success).toBe(true);
    });

    it('handles a 404 gracefully', async () => {
      get_request.mockRejectedValue(new Error('Not found'));

      const result = await store.fetchPublicLinktree('nadie');

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('createLinktree', () => {
    it('creates a linktree and prepends it to the list', async () => {
      create_request.mockResolvedValue({ data: mockLinktree });

      const result = await store.createLinktree({ handle: 'gustavo', name: 'Gustavo' });

      expect(create_request).toHaveBeenCalledWith('linktrees/admin/create/', { handle: 'gustavo', name: 'Gustavo' });
      expect(store.linktrees[0]).toEqual(mockLinktree);
      expect(result.success).toBe(true);
    });

    it('returns validation errors on failure', async () => {
      const error = new Error('Bad request');
      error.response = { data: { handle: ['Este handle ya está en uso.'] } };
      create_request.mockRejectedValue(error);

      const result = await store.createLinktree({ handle: 'gustavo' });

      expect(result.success).toBe(false);
      expect(result.errors).toEqual({ handle: ['Este handle ya está en uso.'] });
      expect(store.error).toBe('create_failed');
    });
  });

  describe('updateLinktree', () => {
    it('updates the linktree in the list in place', async () => {
      store.linktrees = [mockLinktree];
      const updated = { ...mockLinktree, name: 'Renombrado' };
      patch_request.mockResolvedValue({ data: updated });

      const result = await store.updateLinktree(mockLinktree.id, { name: 'Renombrado' });

      expect(patch_request).toHaveBeenCalledWith(`linktrees/admin/${mockLinktree.id}/update/`, { name: 'Renombrado' });
      expect(store.linktrees[0].name).toBe('Renombrado');
      expect(result.success).toBe(true);
    });

    it('refreshes currentLinktree when it is the edited one', async () => {
      store.currentLinktree = { ...mockLinktree, buttons: [] };
      const updated = { ...mockLinktree, name: 'Renombrado', buttons: [] };
      patch_request.mockResolvedValue({ data: updated });

      await store.updateLinktree(mockLinktree.id, { name: 'Renombrado' });

      expect(store.currentLinktree.name).toBe('Renombrado');
    });

    it('handles API error gracefully', async () => {
      patch_request.mockRejectedValue(new Error('Network error'));

      const result = await store.updateLinktree(mockLinktree.id, {});

      expect(result.success).toBe(false);
      expect(store.error).toBe('update_failed');
    });
  });

  describe('uploadAvatar', () => {
    afterEach(() => {
      delete global.fetch;
    });

    it('uploads the file and refreshes currentLinktree', async () => {
      const updated = { ...mockLinktree, avatar: '/media/linktrees/avatars/gp.jpg', buttons: [] };
      global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => updated });

      const result = await store.uploadAvatar(mockLinktree.id, new Blob(['x']));

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/linktrees/admin/${mockLinktree.id}/avatar/`,
        expect.objectContaining({ method: 'POST' })
      );
      expect(store.currentLinktree.avatar).toBe('/media/linktrees/avatars/gp.jpg');
      expect(result.success).toBe(true);
    });

    it('returns backend validation errors on rejection', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ avatar: 'Formato .gif no permitido (usa JPG, PNG o WebP).' }),
      });

      const result = await store.uploadAvatar(mockLinktree.id, new Blob(['x']));

      expect(result.success).toBe(false);
      expect(result.errors.avatar).toContain('no permitido');
    });
  });

  describe('removeAvatar', () => {
    it('clears the avatar via the delete endpoint', async () => {
      const updated = { ...mockLinktree, avatar: null, buttons: [] };
      delete_request.mockResolvedValue({ data: updated });

      const result = await store.removeAvatar(mockLinktree.id);

      expect(delete_request).toHaveBeenCalledWith(`linktrees/admin/${mockLinktree.id}/avatar/`);
      expect(store.currentLinktree.avatar).toBeNull();
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      delete_request.mockRejectedValue(new Error('Network error'));

      const result = await store.removeAvatar(mockLinktree.id);

      expect(result.success).toBe(false);
      expect(store.error).toBe('upload_failed');
    });
  });

  describe('deleteLinktree', () => {
    it('removes the linktree from the list', async () => {
      store.linktrees = [mockLinktree];
      delete_request.mockResolvedValue({});

      const result = await store.deleteLinktree(mockLinktree.id);

      expect(delete_request).toHaveBeenCalledWith(`linktrees/admin/${mockLinktree.id}/delete/`);
      expect(store.linktrees).toHaveLength(0);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      delete_request.mockRejectedValue(new Error('Network error'));

      const result = await store.deleteLinktree(mockLinktree.id);

      expect(result.success).toBe(false);
      expect(store.error).toBe('delete_failed');
    });
  });
});

/**
 * Tests for the linkedin store.
 *
 * Covers: OAuth connection actions (fetchLinkedInStatus, fetchLinkedInAuthUrl,
 * linkedinCallback) and freeform posts CRUD (fetchPosts, createPost,
 * updatePost, deletePost, publishPost).
 *
 * NOTE: LinkedIn actions are mocked at the request layer (get_request/create_request).
 * No real LinkedIn API calls are made. Do NOT add fixtures that store real tokens
 * or call linkedin.com — the production LinkedInToken singleton is a real account.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useLinkedInStore } from '../../stores/linkedin';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  put_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, put_request, delete_request,
} = require('../../stores/services/request_http');

describe('useLinkedInStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useLinkedInStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has empty posts and disconnected status', () => {
      expect(store.posts).toEqual([]);
      expect(store.connectionStatus).toEqual({ connected: false });
    });
  });

  describe('OAuth actions', () => {
    it('fetchLinkedInStatus returns connected status and stores it', async () => {
      const statusData = {
        connected: true,
        profile_name: 'Gustavo',
        profile_email: 'g@example.com',
        expires_at: '2026-09-01T00:00:00Z',
      };
      get_request.mockResolvedValue({ data: statusData });

      const result = await store.fetchLinkedInStatus();

      expect(get_request).toHaveBeenCalledWith('linkedin/status/');
      expect(result.success).toBe(true);
      expect(result.data).toEqual(statusData);
      expect(store.connectionStatus).toEqual(statusData);
    });

    it('fetchLinkedInStatus returns failure on network error', async () => {
      get_request.mockRejectedValue(new Error('network'));

      const result = await store.fetchLinkedInStatus();

      expect(result.success).toBe(false);
    });

    it('fetchLinkedInAuthUrl returns authorization URL on success', async () => {
      const urlData = { authorization_url: 'https://linkedin.com/oauth', state: 'abc123' };
      get_request.mockResolvedValue({ data: urlData });

      const result = await store.fetchLinkedInAuthUrl();

      expect(get_request).toHaveBeenCalledWith('linkedin/auth-url/');
      expect(result.success).toBe(true);
      expect(result.data).toEqual(urlData);
    });

    it('fetchLinkedInAuthUrl returns failure on network error', async () => {
      get_request.mockRejectedValue(new Error('network'));

      const result = await store.fetchLinkedInAuthUrl();

      expect(result.success).toBe(false);
    });

    it('linkedinCallback sends code and state, returns connection data on success', async () => {
      const connectionData = { connection: { connected: true, profile_name: 'Gustavo' } };
      create_request.mockResolvedValue({ data: connectionData });

      const result = await store.linkedinCallback('auth-code-123', 'state-xyz');

      expect(create_request).toHaveBeenCalledWith('linkedin/callback/', { code: 'auth-code-123', state: 'state-xyz' });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(connectionData);
    });

    it('linkedinCallback returns failure with error message on API error', async () => {
      create_request.mockRejectedValue({ response: { data: { error: 'Invalid state token.' } } });

      const result = await store.linkedinCallback('bad-code', 'bad-state');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid state token.');
    });

    it('linkedinCallback returns failure without error property on network error', async () => {
      create_request.mockRejectedValue(new Error('network'));

      const result = await store.linkedinCallback('code', 'state');

      expect(result.success).toBe(false);
      expect(result.error).toBeUndefined();
    });
  });

  describe('posts CRUD', () => {
    it('fetchPosts stores the list', async () => {
      get_request.mockResolvedValue({ data: [{ id: 1, commentary: 'Hola', status: 'draft' }] });

      const result = await store.fetchPosts();

      expect(get_request).toHaveBeenCalledWith('linkedin/posts/');
      expect(result.success).toBe(true);
      expect(store.posts).toHaveLength(1);
    });

    it('fetchPosts returns failure on network error', async () => {
      get_request.mockRejectedValue(new Error('network'));

      const result = await store.fetchPosts();

      expect(result.success).toBe(false);
      expect(store.posts).toEqual([]);
    });

    it('createPost posts to the create endpoint', async () => {
      create_request.mockResolvedValue({ data: { id: 2, status: 'draft' } });

      const result = await store.createPost({ commentary: 'Nuevo' });

      expect(create_request).toHaveBeenCalledWith('linkedin/posts/create/', { commentary: 'Nuevo' });
      expect(result.success).toBe(true);
    });

    it('createPost returns backend validation errors', async () => {
      create_request.mockRejectedValue({ response: { data: { scheduled_at: ['La fecha programada debe estar en el futuro.'] } } });

      const result = await store.createPost({ commentary: 'x', scheduled_at: '2020-01-01' });

      expect(result.success).toBe(false);
      expect(result.error.scheduled_at).toBeDefined();
    });

    it('updatePost puts to the update endpoint', async () => {
      put_request.mockResolvedValue({ data: { id: 2, status: 'draft' } });

      await store.updatePost(2, { commentary: 'Edit' });

      expect(put_request).toHaveBeenCalledWith('linkedin/posts/2/update/', { commentary: 'Edit' });
    });

    it('deletePost calls the delete endpoint', async () => {
      delete_request.mockResolvedValue({});

      const result = await store.deletePost(3);

      expect(delete_request).toHaveBeenCalledWith('linkedin/posts/3/delete/');
      expect(result.success).toBe(true);
    });

    it('publishPost posts to the publish endpoint', async () => {
      create_request.mockResolvedValue({ data: { id: 4, status: 'published' } });

      const result = await store.publishPost(4);

      expect(create_request).toHaveBeenCalledWith('linkedin/posts/4/publish/', {});
      expect(result.success).toBe(true);
    });

    it('publishPost surfaces backend error message', async () => {
      create_request.mockRejectedValue({ response: { data: { error: 'ya publicado' } } });

      const result = await store.publishPost(4);

      expect(result.success).toBe(false);
      expect(result.error).toBe('ya publicado');
    });
  });
});

/**
 * Tests for the blog store.
 *
 * Covers: fetchPosts, fetchPost, fetchAdminPosts, fetchAdminPost,
 * createPost, updatePost, deletePost, getters, error handling.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useBlogStore } from '../../stores/blog';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

describe('useBlogStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useBlogStore();
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('has empty posts array', () => {
      expect(store.posts).toEqual([]);
    });

    it('has null currentPost', () => {
      expect(store.currentPost).toBeNull();
    });

    it('has isLoading false', () => {
      expect(store.isLoading).toBe(false);
    });
  });

  describe('getters', () => {
    it('featuredPost returns first post', () => {
      store.posts = [{ id: 1 }, { id: 2 }];
      expect(store.featuredPost).toEqual({ id: 1 });
    });

    it('featuredPost returns null when empty', () => {
      expect(store.featuredPost).toBeNull();
    });

    it('otherPosts returns all except first', () => {
      store.posts = [{ id: 1 }, { id: 2 }, { id: 3 }];
      expect(store.otherPosts).toEqual([{ id: 2 }, { id: 3 }]);
    });

    it('getPostById finds post by id', () => {
      store.posts = [{ id: 1, title: 'A' }, { id: 2, title: 'B' }];
      expect(store.getPostById(2)).toEqual({ id: 2, title: 'B' });
    });

    it('getPostById returns undefined for missing id', () => {
      store.posts = [{ id: 1 }];
      expect(store.getPostById(99)).toBeUndefined();
    });
  });

  describe('fetchPosts', () => {
    it('fetches posts with lang param', async () => {
      get_request.mockResolvedValue({ data: [{ id: 1 }] });

      const result = await store.fetchPosts('en');

      expect(get_request).toHaveBeenCalledWith('blog/?lang=en');
      expect(store.posts).toEqual([{ id: 1 }]);
      expect(result.success).toBe(true);
    });

    it('defaults to es language', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.fetchPosts();

      expect(get_request).toHaveBeenCalledWith('blog/?lang=es');
    });

    it('handles error and sets error state', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchPosts();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
      expect(store.isLoading).toBe(false);
    });
  });

  describe('fetchPost', () => {
    it('fetches single post by slug', async () => {
      const postData = { id: 1, title: 'Test' };
      get_request.mockResolvedValue({ data: postData });

      const result = await store.fetchPost('test-slug', 'en');

      expect(get_request).toHaveBeenCalledWith('blog/test-slug/?lang=en');
      expect(store.currentPost).toEqual(postData);
      expect(result.success).toBe(true);
    });

    it('sets not_found error on 404', async () => {
      get_request.mockRejectedValue({ response: { status: 404 } });

      const result = await store.fetchPost('missing');

      expect(result.success).toBe(false);
      expect(store.error).toBe('not_found');
    });

    it('sets unknown error on other status', async () => {
      get_request.mockRejectedValue({ response: { status: 500 } });

      const result = await store.fetchPost('error-slug');

      expect(store.error).toBe('unknown');
    });
  });

  describe('admin actions', () => {
    it('fetchAdminPosts fetches all posts', async () => {
      get_request.mockResolvedValue({ data: [{ id: 1 }, { id: 2 }] });

      const result = await store.fetchAdminPosts();

      expect(get_request).toHaveBeenCalledWith('blog/admin/');
      expect(store.posts).toHaveLength(2);
      expect(result.success).toBe(true);
    });

    it('fetchAdminPost fetches single post by id', async () => {
      get_request.mockResolvedValue({ data: { id: 5 } });

      const result = await store.fetchAdminPost(5);

      expect(get_request).toHaveBeenCalledWith('blog/admin/5/detail/');
      expect(store.currentPost).toEqual({ id: 5 });
    });

    it('createPost sends payload and sets currentPost', async () => {
      const newPost = { id: 10, title_es: 'Nuevo' };
      create_request.mockResolvedValue({ data: newPost });

      const result = await store.createPost({ title_es: 'Nuevo' });

      expect(create_request).toHaveBeenCalledWith('blog/admin/create/', { title_es: 'Nuevo' });
      expect(store.currentPost).toEqual(newPost);
      expect(result.success).toBe(true);
    });

    it('createPost handles validation error', async () => {
      create_request.mockRejectedValue({
        response: { data: { title_es: ['Required'] } },
      });

      const result = await store.createPost({});

      expect(result.success).toBe(false);
      expect(store.error).toBe('create_failed');
    });

    it('updatePost patches and updates currentPost', async () => {
      patch_request.mockResolvedValue({ data: { id: 1, title_en: 'Updated' } });

      const result = await store.updatePost(1, { title_en: 'Updated' });

      expect(patch_request).toHaveBeenCalledWith('blog/admin/1/update/', { title_en: 'Updated' });
      expect(result.success).toBe(true);
    });

    it('deletePost removes post from list', async () => {
      store.posts = [{ id: 1 }, { id: 2 }];
      delete_request.mockResolvedValue({});

      const result = await store.deletePost(1);

      expect(delete_request).toHaveBeenCalledWith('blog/admin/1/delete/');
      expect(store.posts).toEqual([{ id: 2 }]);
      expect(result.success).toBe(true);
    });

    it('deletePost clears currentPost if matching', async () => {
      store.currentPost = { id: 1 };
      store.posts = [{ id: 1 }];
      delete_request.mockResolvedValue({});

      await store.deletePost(1);

      expect(store.currentPost).toBeNull();
    });
  });
});

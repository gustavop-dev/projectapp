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
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
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
    it('featuredPost returns post with is_featured flag', () => {
      store.posts = [{ id: 1 }, { id: 2, is_featured: true }, { id: 3 }];
      expect(store.featuredPost).toEqual({ id: 2, is_featured: true });
    });

    it('featuredPost falls back to first post when none is_featured', () => {
      store.posts = [{ id: 1 }, { id: 2 }];
      expect(store.featuredPost).toEqual({ id: 1 });
    });

    it('featuredPost returns null when empty', () => {
      expect(store.featuredPost).toBeNull();
    });

    it('otherPosts returns all except the featured one', () => {
      store.posts = [{ id: 1 }, { id: 2, is_featured: true }, { id: 3 }];
      expect(store.otherPosts).toEqual([{ id: 1 }, { id: 3 }]);
    });

    it('otherPosts returns all except first when none is_featured', () => {
      store.posts = [{ id: 1 }, { id: 2 }, { id: 3 }];
      expect(store.otherPosts).toEqual([{ id: 2 }, { id: 3 }]);
    });

    it('otherPosts returns empty array when no posts', () => {
      store.posts = [];
      expect(store.otherPosts).toEqual([]);
    });

    it('categories returns unique sorted category values', () => {
      store.posts = [
        { id: 1, category: 'design' },
        { id: 2, category: 'ai' },
        { id: 3, category: 'design' },
        { id: 4, category: '' },
      ];
      expect(store.categories).toEqual(['ai', 'design']);
    });

    it('categories returns empty array when no posts', () => {
      expect(store.categories).toEqual([]);
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

      const _result = await store.fetchPost('error-slug');

      expect(store.error).toBe('unknown');
    });

    it('sets unknown error when error has no response property', async () => {
      get_request.mockRejectedValue(new Error('network'));

      const result = await store.fetchPost('slug');

      expect(result.success).toBe(false);
      expect(store.error).toBe('unknown');
      expect(result.status).toBeUndefined();
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

    it('fetchAdminPosts handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchAdminPosts();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
      expect(store.isLoading).toBe(false);
    });

    it('fetchAdminPost fetches single post by id', async () => {
      get_request.mockResolvedValue({ data: { id: 5 } });

      const _result = await store.fetchAdminPost(5);

      expect(get_request).toHaveBeenCalledWith('blog/admin/5/detail/');
      expect(store.currentPost).toEqual({ id: 5 });
    });

    it('fetchAdminPost handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchAdminPost(99);

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
      expect(store.isLoading).toBe(false);
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

    it('createPost handles error without response property', async () => {
      create_request.mockRejectedValue(new Error('network'));

      const result = await store.createPost({});

      expect(result.success).toBe(false);
      expect(result.errors).toBeUndefined();
    });

    it('updatePost patches and updates currentPost', async () => {
      patch_request.mockResolvedValue({ data: { id: 1, title_en: 'Updated' } });

      const result = await store.updatePost(1, { title_en: 'Updated' });

      expect(patch_request).toHaveBeenCalledWith('blog/admin/1/update/', { title_en: 'Updated' });
      expect(result.success).toBe(true);
    });

    it('updatePost handles error', async () => {
      patch_request.mockRejectedValue({
        response: { data: { title_es: ['Required'] } },
      });

      const result = await store.updatePost(1, {});

      expect(result.success).toBe(false);
      expect(store.error).toBe('update_failed');
      expect(store.isUpdating).toBe(false);
    });

    it('updatePost handles error without response property', async () => {
      patch_request.mockRejectedValue(new Error('network'));

      const result = await store.updatePost(1, {});

      expect(result.success).toBe(false);
      expect(result.errors).toBeUndefined();
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

    it('deletePost keeps null currentPost unchanged', async () => {
      store.currentPost = null;
      store.posts = [{ id: 1 }];
      delete_request.mockResolvedValue({});

      await store.deletePost(1);

      expect(store.currentPost).toBeNull();
      expect(store.posts).toEqual([]);
    });

    it('deletePost handles error', async () => {
      delete_request.mockRejectedValue(new Error('fail'));

      const result = await store.deletePost(1);

      expect(result.success).toBe(false);
      expect(store.error).toBe('delete_failed');
      expect(store.isUpdating).toBe(false);
    });

    it('createPostFromJSON sends payload and sets currentPost', async () => {
      const newPost = { id: 20, title_es: 'JSON Post' };
      create_request.mockResolvedValue({ data: newPost });

      const result = await store.createPostFromJSON({ title_es: 'JSON Post', content_json_es: {} });

      expect(create_request).toHaveBeenCalledWith(
        'blog/admin/create-from-json/',
        { title_es: 'JSON Post', content_json_es: {} },
      );
      expect(store.currentPost).toEqual(newPost);
      expect(result.success).toBe(true);
    });

    it('createPostFromJSON handles error', async () => {
      create_request.mockRejectedValue({
        response: { data: { content_json_es: ['Invalid'] } },
      });

      const result = await store.createPostFromJSON({});

      expect(result.success).toBe(false);
      expect(store.error).toBe('create_failed');
      expect(store.isUpdating).toBe(false);
    });

    it('createPostFromJSON handles error without response property', async () => {
      create_request.mockRejectedValue(new Error('network'));

      const result = await store.createPostFromJSON({});

      expect(result.success).toBe(false);
      expect(result.errors).toBeUndefined();
    });

    it('uploads image file and sets currentPost on success', async () => {
      const responseData = { id: 1, cover_image: '/media/cover.jpg' };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(responseData),
      });
      Object.defineProperty(document, 'cookie', {
        value: 'csrftoken=abc123',
        writable: true,
      });
      const file = new File(['img'], 'cover.jpg', { type: 'image/jpeg' });

      const result = await store.uploadCoverImage(1, file);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/blog/admin/1/upload-cover/',
        expect.objectContaining({ method: 'POST' }),
      );
      expect(result.success).toBe(true);
      expect(store.currentPost).toEqual(responseData);
    });

    it('sets upload_failed error when server returns non-ok response', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false });

      const file = new File(['img'], 'cover.jpg', { type: 'image/jpeg' });
      const result = await store.uploadCoverImage(1, file);

      expect(result.success).toBe(false);
      expect(store.error).toBe('upload_failed');
    });

    it('sets upload_failed error on network failure', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('network'));

      const file = new File(['img'], 'cover.jpg', { type: 'image/jpeg' });
      const result = await store.uploadCoverImage(1, file);

      expect(result.success).toBe(false);
      expect(store.error).toBe('upload_failed');
    });

    it('duplicatePost sends POST and prepends to list', async () => {
      const duplicated = { id: 99, title_es: 'Post (copia)' };
      create_request.mockResolvedValue({ data: duplicated });
      store.posts = [{ id: 1 }];

      const result = await store.duplicatePost(1);

      expect(create_request).toHaveBeenCalledWith('blog/admin/1/duplicate/', {});
      expect(result.success).toBe(true);
      expect(result.data).toEqual(duplicated);
      expect(store.posts[0]).toEqual(duplicated);
      expect(store.posts).toHaveLength(2);
    });

    it('duplicatePost handles error', async () => {
      create_request.mockRejectedValue(new Error('fail'));

      const result = await store.duplicatePost(1);

      expect(result.success).toBe(false);
      expect(store.error).toBe('duplicate_failed');
      expect(store.isUpdating).toBe(false);
    });

    it('fetchCategories fetches and stores available categories', async () => {
      const cats = [{ slug: 'ai', label: 'AI' }, { slug: 'design', label: 'Design' }];
      get_request.mockResolvedValue({ data: { _available_categories: cats } });

      const result = await store.fetchCategories();

      expect(get_request).toHaveBeenCalledWith('blog/admin/json-template/');
      expect(result.success).toBe(true);
      expect(store.availableCategories).toEqual(cats);
    });

    it('fetchCategories defaults to empty array when key missing', async () => {
      get_request.mockResolvedValue({ data: {} });

      const result = await store.fetchCategories();

      expect(result.success).toBe(true);
      expect(store.availableCategories).toEqual([]);
    });

    it('fetchCategories handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchCategories();

      expect(result.success).toBe(false);
    });

    it('downloadJSONTemplate returns template data', async () => {
      const templateData = { title_es: 'Template', content_json_es: { intro: 'I' } };
      get_request.mockResolvedValue({ data: templateData });

      const result = await store.downloadJSONTemplate();

      expect(get_request).toHaveBeenCalledWith('blog/admin/json-template/');
      expect(result.success).toBe(true);
      expect(result.data).toEqual(templateData);
    });

    it('downloadJSONTemplate handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.downloadJSONTemplate();

      expect(result.success).toBe(false);
    });
  });
});

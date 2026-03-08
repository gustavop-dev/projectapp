import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useBlogStore = defineStore('blog', {
  /**
   * State of the Blog store.
   *
   * Properties:
   * - posts (Array): List of blog posts.
   * - currentPost (Object|null): Currently viewed/edited post.
   * - isLoading (Boolean): Whether a fetch operation is in progress.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   * - error (String|null): Last error message.
   */
  state: () => ({
    posts: [],
    currentPost: null,
    availableCategories: [],
    pagination: { count: 0, page: 1, pageSize: 6, totalPages: 1 },
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * featuredPost: Post explicitly marked as featured, or the most recent.
     */
    featuredPost: (state) => {
      const pinned = state.posts.find((p) => p.is_featured);
      return pinned || state.posts[0] || null;
    },

    /**
     * otherPosts: All posts except the featured one.
     */
    otherPosts(state) {
      const featured = this.featuredPost;
      if (!featured) return state.posts;
      return state.posts.filter((p) => p.id !== featured.id);
    },

    /**
     * categories: Unique category values extracted from the post list.
     */
    categories: (state) => {
      const cats = new Set();
      state.posts.forEach((p) => { if (p.category) cats.add(p.category); });
      return [...cats].sort();
    },

    /**
     * getPostById: Find a post in the list by its ID.
     */
    getPostById: (state) => (id) =>
      state.posts.find((p) => p.id === id),
  },

  actions: {
    // -----------------------------------------------------------------
    // Public
    // -----------------------------------------------------------------

    /**
     * fetchPosts: List all published blog posts.
     * @param {string} lang - Language code ('es' or 'en').
     */
    async fetchPosts(lang = 'es', page = 1, pageSize = 6) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`blog/?lang=${lang}&page=${page}&page_size=${pageSize}`);
        const data = response.data;
        this.posts = data.results || data;
        this.pagination = {
          count: data.count || this.posts.length,
          page: data.page || 1,
          pageSize: data.page_size || pageSize,
          totalPages: data.total_pages || 1,
        };
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching blog posts:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchPost: Retrieve a single published blog post by slug.
     * @param {string} slug - Post slug.
     * @param {string} lang - Language code ('es' or 'en').
     */
    async fetchPost(slug, lang = 'es') {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`blog/${slug}/?lang=${lang}`);
        this.currentPost = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        const status = error.response?.status;
        if (status === 404) {
          this.error = 'not_found';
        } else {
          this.error = 'unknown';
        }
        return { success: false, error: this.error, status };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    // -----------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------

    /**
     * fetchAdminPosts: List all blog posts (including drafts) for admin.
     */
    async fetchAdminPosts() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('blog/admin/');
        this.posts = response.data;
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching admin blog posts:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * fetchAdminPost: Retrieve full post detail for admin editing.
     * @param {number} id - Post ID.
     */
    async fetchAdminPost(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`blog/admin/${id}/detail/`);
        this.currentPost = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching blog post:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * createPost: Create a new blog post.
     * @param {object} payload - Post data.
     */
    async createPost(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('blog/admin/create/', payload);
        this.currentPost = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating blog post:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * updatePost: Update a blog post's fields.
     * @param {number} id - Post ID.
     * @param {object} payload - Fields to update.
     */
    async updatePost(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`blog/admin/${id}/update/`, payload);
        this.currentPost = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating blog post:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * deletePost: Delete a blog post.
     * @param {number} id - Post ID.
     */
    async deletePost(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`blog/admin/${id}/delete/`);
        this.posts = this.posts.filter((p) => p.id !== id);
        if (this.currentPost?.id === id) {
          this.currentPost = null;
        }
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting blog post:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * createPostFromJSON: Create a blog post from a full JSON payload.
     * @param {object} payload - Full blog JSON including content_json.
     */
    async createPostFromJSON(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('blog/admin/create-from-json/', payload);
        this.currentPost = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating blog post from JSON:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * uploadCoverImage: Upload a cover image file for a blog post.
     * @param {number} id - Post ID.
     * @param {File} file - Image file to upload.
     */
    async uploadCoverImage(id, file) {
      this.isUpdating = true;
      this.error = null;
      try {
        const formData = new FormData();
        formData.append('cover_image', file);
        const csrfToken = document.cookie
          .split('; ')
          .find((c) => c.startsWith('csrftoken='))
          ?.split('=')[1] || '';
        const response = await fetch(`/api/blog/admin/${id}/upload-cover/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          body: formData,
        });
        if (!response.ok) throw new Error('Upload failed');
        const data = await response.json();
        this.currentPost = data;
        return { success: true, data };
      } catch (error) {
        this.error = 'upload_failed';
        console.error('Error uploading cover image:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * duplicatePost: Create a deep copy of a blog post as a new draft.
     * @param {number} id - Post ID to duplicate.
     */
    async duplicatePost(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request(`blog/admin/${id}/duplicate/`, {});
        this.posts.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'duplicate_failed';
        console.error('Error duplicating blog post:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    /**
     * fetchCategories: Fetch available categories from the JSON template endpoint.
     */
    async fetchCategories() {
      try {
        const response = await get_request('blog/admin/json-template/');
        this.availableCategories = response.data._available_categories || [];
        return { success: true };
      } catch (error) {
        console.error('Error fetching blog categories:', error);
        return { success: false };
      }
    },

    /**
     * downloadJSONTemplate: Fetch the blog JSON template from the API.
     */
    async downloadJSONTemplate() {
      try {
        const response = await get_request('blog/admin/json-template/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error downloading blog JSON template:', error);
        return { success: false };
      }
    },
  },
});

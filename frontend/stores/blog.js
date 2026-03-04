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
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    /**
     * featuredPost: The most recent published post (first in the list).
     */
    featuredPost: (state) => state.posts[0] || null,

    /**
     * otherPosts: All posts except the featured one.
     */
    otherPosts: (state) => state.posts.slice(1),

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
    async fetchPosts(lang = 'es') {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`blog/?lang=${lang}`);
        this.posts = response.data;
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching blog posts:', error);
        return { success: false };
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
      } finally {
        this.isUpdating = false;
      }
    },
  },
});

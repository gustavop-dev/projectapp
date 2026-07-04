import { defineStore } from 'pinia';
import {
  get_request,
  create_request,
  put_request,
  delete_request,
} from '~/stores/services/request_http';

/**
 * LinkedIn integration store: OAuth connection + freeform posts
 * managed from /panel/linkedin. Blog-post publishing stays in the
 * blog store (it is a BlogPost-scoped endpoint).
 */
export const useLinkedInStore = defineStore('linkedin', {
  state: () => ({
    posts: [],
    connectionStatus: { connected: false },
  }),

  getters: {},

  actions: {
    /**
     * fetchLinkedInStatus: Check LinkedIn connection status.
     * @returns {Promise<Object>} - { success, data } with connection info.
     */
    async fetchLinkedInStatus() {
      try {
        const response = await get_request('linkedin/status/');
        this.connectionStatus = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn status:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * fetchLinkedInAuthUrl: Get the LinkedIn OAuth authorization URL.
     * @returns {Promise<Object>} - { success, data } with authorization_url.
     */
    async fetchLinkedInAuthUrl() {
      try {
        const response = await get_request('linkedin/auth-url/');
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn auth URL:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * linkedinCallback: Exchange authorization code for token.
     * @param {string} code - Authorization code from LinkedIn redirect.
     * @param {string} state - CSRF state from the auth URL.
     * @returns {Promise<Object>} - { success, data } with connection info.
     */
    async linkedinCallback(code, state) {
      try {
        const response = await create_request('linkedin/callback/', { code, state });
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error exchanging LinkedIn code:', error);
        return { success: false, error: error.response?.data?.error };
      }
    },

    /**
     * fetchPosts: List freeform LinkedIn posts (newest first).
     * @returns {Promise<Object>} - { success, data } with the posts array.
     */
    async fetchPosts() {
      try {
        const response = await get_request('linkedin/posts/');
        this.posts = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching LinkedIn posts:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * createPost: Create a draft/scheduled post. Accepts FormData
     * (commentary, optional image file, optional scheduled_at ISO).
     * @param {FormData|Object} formData - Post payload.
     * @returns {Promise<Object>} - { success, data } with the created post.
     */
    async createPost(formData) {
      try {
        const response = await create_request('linkedin/posts/create/', formData);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error creating LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * updatePost: Update a non-published post.
     * @param {number} id - Post id.
     * @param {FormData|Object} formData - Post payload.
     * @returns {Promise<Object>} - { success, data } with the updated post.
     */
    async updatePost(id, formData) {
      try {
        const response = await put_request(`linkedin/posts/${id}/update/`, formData);
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error updating LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * deletePost: Delete a post (local record only).
     * @param {number} id - Post id.
     * @returns {Promise<Object>} - { success }.
     */
    async deletePost(id) {
      try {
        await delete_request(`linkedin/posts/${id}/delete/`);
        return { success: true };
      } catch (error) {
        console.error('Error deleting LinkedIn post:', error);
        return { success: false, error: error.response?.data };
      }
    },

    /**
     * publishPost: Publish a post to LinkedIn immediately.
     * @param {number} id - Post id.
     * @returns {Promise<Object>} - { success, data } with the updated post.
     */
    async publishPost(id) {
      try {
        const response = await create_request(`linkedin/posts/${id}/publish/`, {});
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error publishing LinkedIn post:', error);
        return { success: false, error: error.response?.data?.error };
      }
    },
  },
});

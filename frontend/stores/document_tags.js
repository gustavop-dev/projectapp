import { defineStore } from 'pinia';
import {
  get_request, create_request, patch_request, delete_request,
} from './services/request_http';

export const useDocumentTagStore = defineStore('documentTags', {
  state: () => ({
    tags: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  actions: {
    async fetchTags() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('document-tags/');
        this.tags = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_tags_failed';
        console.error('Error fetching tags:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createTag(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('document-tags/create/', payload);
        this.tags.push(response.data);
        this.tags.sort((a, b) => a.name.localeCompare(b.name));
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_tag_failed';
        console.error('Error creating tag:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateTag(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-tags/${id}/update/`, payload);
        const idx = this.tags.findIndex((t) => t.id === id);
        if (idx !== -1) this.tags.splice(idx, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_tag_failed';
        console.error('Error updating tag:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteTag(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`document-tags/${id}/delete/`);
        this.tags = this.tags.filter((t) => t.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_tag_failed';
        console.error('Error deleting tag:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});

import { defineStore } from 'pinia';
import {
  get_request, create_request, patch_request, delete_request,
} from './services/request_http';

export const useDocumentFolderStore = defineStore('documentFolders', {
  state: () => ({
    folders: [],
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  actions: {
    async fetchFolders() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('document-folders/');
        this.folders = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_folders_failed';
        console.error('Error fetching folders:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createFolder(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('document-folders/create/', payload);
        this.folders.push(response.data);
        this.folders.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name));
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_folder_failed';
        console.error('Error creating folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateFolder(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`document-folders/${id}/update/`, payload);
        const idx = this.folders.findIndex((f) => f.id === id);
        if (idx !== -1) this.folders.splice(idx, 1, response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_folder_failed';
        console.error('Error updating folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteFolder(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`document-folders/${id}/delete/`);
        this.folders = this.folders.filter((f) => f.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_folder_failed';
        console.error('Error deleting folder:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async reorderFolders(orderedIds) {
      this.isUpdating = true;
      this.error = null;
      try {
        await create_request('document-folders/reorder/', { ids: orderedIds });
        const reordered = orderedIds.map((id) => this.folders.find((f) => f.id === id)).filter(Boolean);
        if (reordered.length === this.folders.length) this.folders = reordered;
        return { success: true };
      } catch (error) {
        console.error('Error reordering folders:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});

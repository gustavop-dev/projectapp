import { defineStore } from 'pinia';
import { get_request, create_request, patch_request, delete_request } from './services/request_http';

export const useLinktreesStore = defineStore('linktrees', {
  state: () => ({
    linktrees: [],
    currentLinktree: null,
    publicLinktree: null,
    isLoading: false,
    isUpdating: false,
    error: null,
  }),

  getters: {
    getLinktreeById: (state) => (id) => state.linktrees.find((l) => l.id === id),
  },

  actions: {
    async fetchLinktrees() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request('linktrees/admin/');
        this.linktrees = response.data || [];
        return { success: true };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching linktrees:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async fetchLinktree(id) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`linktrees/admin/${id}/`);
        this.currentLinktree = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching linktree:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async fetchPublicLinktree(handle) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await get_request(`linktrees/public/${encodeURIComponent(handle)}/`);
        this.publicLinktree = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'fetch_failed';
        console.error('Error fetching public linktree:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isLoading = false;
      }
    },

    async createLinktree(payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await create_request('linktrees/admin/create/', payload);
        this.linktrees.unshift(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'create_failed';
        console.error('Error creating linktree:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async updateLinktree(id, payload) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await patch_request(`linktrees/admin/${id}/update/`, payload);
        const index = this.linktrees.findIndex((l) => l.id === id);
        if (index !== -1) this.linktrees[index] = response.data;
        if (this.currentLinktree?.id === id) this.currentLinktree = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'update_failed';
        console.error('Error updating linktree:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async uploadAvatar(id, file) {
      this.isUpdating = true;
      this.error = null;
      try {
        const formData = new FormData();
        formData.append('avatar', file);
        const csrfToken = document.cookie
          .split('; ')
          .find((c) => c.startsWith('csrftoken='))
          ?.split('=')[1] || '';
        const response = await fetch(`/api/linktrees/admin/${id}/avatar/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          body: formData,
        });
        const data = await response.json();
        if (!response.ok) return { success: false, errors: data };
        this.currentLinktree = data;
        return { success: true, data };
      } catch (error) {
        this.error = 'upload_failed';
        console.error('Error uploading linktree avatar:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async removeAvatar(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        const response = await delete_request(`linktrees/admin/${id}/avatar/`);
        this.currentLinktree = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        this.error = 'upload_failed';
        console.error('Error removing linktree avatar:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },

    async deleteLinktree(id) {
      this.isUpdating = true;
      this.error = null;
      try {
        await delete_request(`linktrees/admin/${id}/delete/`);
        this.linktrees = this.linktrees.filter((l) => l.id !== id);
        return { success: true };
      } catch (error) {
        this.error = 'delete_failed';
        console.error('Error deleting linktree:', error);
        return { success: false };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});

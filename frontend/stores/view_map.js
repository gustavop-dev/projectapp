import { defineStore } from 'pinia';
import { get_request, patch_request } from './services/request_http';

export const useViewMapStore = defineStore('view_map', {
  /**
   * State of the ViewMap store (panel settings singleton).
   *
   * Properties:
   * - settings (Object|null): { default_view_mode, default_filters, updated_at }.
   * - isUpdating (Boolean): Whether a mutation operation is in progress.
   */
  state: () => ({
    settings: null,
    isUpdating: false,
  }),

  actions: {
    /**
     * fetchSettings: Load the view-map panel settings singleton.
     */
    async fetchSettings() {
      try {
        const response = await get_request('view-map/admin/settings/');
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error fetching view map settings:', error);
        return { success: false };
      }
    },

    /**
     * updateSettings: Patch the settings singleton
     * (default_view_mode and/or default_filters).
     * @param {object} payload - Fields to update.
     */
    async updateSettings(payload) {
      this.isUpdating = true;
      try {
        const response = await patch_request('view-map/admin/settings/update/', payload);
        this.settings = response.data;
        return { success: true, data: response.data };
      } catch (error) {
        console.error('Error updating view map settings:', error);
        return { success: false, errors: error.response?.data };
      /* c8 ignore next 3 */
      } finally {
        this.isUpdating = false;
      }
    },
  },
});
